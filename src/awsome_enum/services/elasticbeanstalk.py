from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta
import boto3

class ElasticBeanstalkService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'elasticbeanstalk', debug)
        self.supported_actions = [
            "elasticbeanstalk:*",
            "elasticbeanstalk:DescribeApplications",
            "elasticbeanstalk:DescribeApplicationVersions",
            "elasticbeanstalk:DescribeEnvironments",
            "elasticbeanstalk:DescribeEnvironmentResources",
            "elasticbeanstalk:DescribeEvents"
        ]
        self.find_all_s3_buckets = False

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating Elastic Beanstalk Resources")
        print_cyan("*" * 80)

        try:
            # Check for S3 buckets in all regions
            self._handle_check_s3_buckets()
            self._handle_describe_applications("elasticbeanstalk:DescribeApplications", "*")
            self._handle_describe_application_versions("elasticbeanstalk:DescribeApplicationVersions", "*")
            self._handle_describe_environments("elasticbeanstalk:DescribeEnvironments", "*")
            self._handle_describe_events("elasticbeanstalk:DescribeEvents", "*")
        except Exception as e:
            print_red(f"Error enumerating Elastic Beanstalk resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        # Check for S3 buckets in all regions
        self._handle_check_s3_buckets()
        
        if "elasticbeanstalk:DescribeApplications" == action or "elasticbeanstalk:*" == action:
            self._handle_describe_applications(action, resource)
        elif "elasticbeanstalk:DescribeApplicationVersions" == action or "elasticbeanstalk:*" == action:
            self._handle_describe_application_versions(action, resource)
        elif "elasticbeanstalk:DescribeEnvironments" == action or "elasticbeanstalk:*" == action:
            self._handle_describe_environments(action, resource)
        elif "elasticbeanstalk:DescribeEnvironmentResources" == action or "elasticbeanstalk:*" == action:
            self._handle_describe_environment_resources(action, resource)
        elif "elasticbeanstalk:DescribeEvents" == action or "elasticbeanstalk:*" == action:
            self._handle_describe_events(action, resource)

    def _handle_check_s3_buckets(self):
        if self.find_all_s3_buckets:
            return
        
        print_yellow("\n[*] Checking Elastic Beanstalk S3 buckets in all regions")
        regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-south-1', 
            'ap-south-2', 'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3', 
            'ap-southeast-1', 'ap-southeast-2', 'ap-southeast-3', 'ca-central-1', 
            'eu-central-1', 'eu-central-2', 'eu-west-1', 'eu-west-2', 'eu-west-3', 
            'eu-north-1', 'sa-east-1', 'af-south-1', 'ap-east-1', 'eu-south-1', 
            'eu-south-2', 'me-south-1', 'me-central-1'
        ]
        
        account_id = self.session.client('sts').get_caller_identity()['Account']
        for region in regions:
            try:
                bucket_name = f"elasticbeanstalk-{region}-{account_id}"
                s3_client = self.session.client('s3')
                s3_client.head_bucket(Bucket=bucket_name)
                print_green(f"Found bucket: {bucket_name}")
            except:
                if self.debug:
                    print_yellow(f"No bucket found in {region}")
        
        self.find_all_s3_buckets = True

    def _handle_describe_applications(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Describing applications")
        try:
            apps = self.describe_applications()
            if apps:
                for app in apps:
                    print_yellow(f"\nApplication: {app.get('ApplicationName')}")
                    app_data = [
                        ['Description', app.get('Description', 'N/A')],
                        ['Date Created', app.get('DateCreated')],
                        ['Date Updated', app.get('DateUpdated')]
                    ]
                    print(tabulate(app_data, tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in applications handler: {str(e)}")

    def _handle_describe_application_versions(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Describing application versions")
        try:
            versions = self.describe_application_versions()
            if versions:
                for version in versions:
                    print_yellow(f"\nApplication Version: {version.get('ApplicationName')} - {version.get('VersionLabel')}")
                    source_bundle = version.get('SourceBundle', {})
                    version_data = [
                        ['S3 Bucket', source_bundle.get('S3Bucket')],
                        ['S3 Key', source_bundle.get('S3Key')],
                        ['Date Created', version.get('DateCreated')],
                        ['Status', version.get('Status')]
                    ]
                    print(tabulate(version_data, tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in application versions handler: {str(e)}")

    def _handle_describe_environments(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Describing environments")
        try:
            envs = self.describe_environments()
            if envs:
                for env in envs:
                    print_yellow(f"\nEnvironment: {env.get('EnvironmentName')}")
                    env_data = [
                        ['Application', env.get('ApplicationName')],
                        ['CNAME', env.get('CNAME')],
                        ['Endpoint URL', env.get('EndpointURL')],
                        ['Status', env.get('Status')],
                        ['Health', env.get('Health')],
                        ['Tier', env.get('Tier', {}).get('Name')]
                    ]
                    print(tabulate(env_data, tablefmt='simple'))
                    # Try to get environment resources
                    self._handle_describe_environment_resources(action, env.get('EnvironmentName'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in environments handler: {str(e)}")

    def _handle_describe_environment_resources(self, action, environment_name):
        try:
            resources = self.describe_environment_resources(environment_name)
            if resources:
                print_yellow(f"\nResources for environment: {environment_name}")
                if resources.get('EnvironmentResources'):
                    for resource_type, items in resources['EnvironmentResources'].items():
                        if items:
                            print_yellow(f"\n{resource_type}:")
                            print(tabulate(items, headers='keys', tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in environment resources handler: {str(e)}")

    def _handle_describe_events(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Describing events")
        try:
            events = self.describe_events()
            if events:
                print_yellow("\nRecent Events:")
                event_data = [[
                    event.get('EventDate'),
                    event.get('Severity'),
                    event.get('EnvironmentName'),
                    event.get('Message')
                ] for event in events]
                print(tabulate(event_data, headers=['Date', 'Severity', 'Environment', 'Message'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in events handler: {str(e)}")

    # API wrapper methods
    def describe_applications(self):
        response = self.client.describe_applications()
        return response.get('Applications', [])

    def describe_application_versions(self):
        response = self.client.describe_application_versions()
        return response.get('ApplicationVersions', [])

    def describe_environments(self):
        response = self.client.describe_environments()
        return response.get('Environments', [])

    def describe_environment_resources(self, environment_name):
        response = self.client.describe_environment_resources(
            EnvironmentName=environment_name
        )
        return response

    def describe_events(self):
        response = self.client.describe_events()
        return response.get('Events', [])
