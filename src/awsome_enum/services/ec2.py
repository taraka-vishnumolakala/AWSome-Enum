import yaml
from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
import base64
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta

class EC2Service(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'ec2', debug)
        self.supported_actions = ["ec2:DescribeInstances", "ec2:Describe*", "ec2:*"]
    
    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating EC2 Resources")
        print_cyan("*" * 80)
        
        try:
            self._list_and_display_instances()
        except Exception as e:
            print_red(f"Error enumerating EC2 resources: {str(e)}")
    
    def handle_permission_action(self, action, resource):
        if "ec2:DescribeInstances" in action or "ec2:Describe*" in action or "ec2:*" in action:
            print_yellow(f"\n[*] Found {action} permission - Listing all instances:\n")
            self._list_and_display_instances()
    
    def _list_and_display_instances(self):
        try:
            instances = self.describe_instances()
            if not instances:
                print_yellow("No EC2 instances found.")
                return

            instance_data = []
            for instance in instances:
                instance_data.append([
                    instance.get('InstanceId'),
                    instance.get('State', {}).get('Name'),
                    instance.get('InstanceType'),
                    instance.get('PublicIpAddress', 'N/A'),
                    instance.get('PrivateIpAddress'),
                    instance.get('IamInstanceProfile', {}).get('Arn', 'N/A')
                ])

            print(tabulate(
                instance_data,
                headers=['Instance ID', 'State', 'Type', 'Public IP', 'Private IP', 'IAM Profile'],
                tablefmt='plain'
            ))

            print_magenta("\n💡 Tip: Use 'awsome-enum --profile [profile] -e ec2 describe-instance-attribute [instance-id] [attribute]'")
            print_magenta("Available attributes: userData, instanceType, groupSet, iamInstanceProfile, rootDeviceName, etc.")
            print_magenta("➡️  More info: https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instance-attribute.html#options")

        except Exception as e:
            print_red(f"Error listing instances: {str(e)}")

    # subcommand methods
    def describe_instance_attribute(self, instance_id, attribute):
        try:
            response = self.client.describe_instance_attribute(
                InstanceId=instance_id,
                Attribute=attribute
            )

            if attribute == 'userData' and 'UserData' in response:
                if 'Value' in response['UserData']:
                    userdata = base64.b64decode(response['UserData']['Value']).decode('utf-8')
                    print_green(f"\n[!] UserData for instance {instance_id}:")
                    print(userdata)
                else:
                    print_yellow(f"No UserData found for instance {instance_id}")
            else:
                print_yellow(f"\n[*] {attribute} for instance {instance_id}:")
                print(yaml.dump(response, default_flow_style=False))

        except ClientError as e:
            print_red(f"Error describing instance attribute: {str(e)}")

    # Wrapper methods for EC2 API calls
    def describe_instances(self):
        response = self.client.describe_instances()
        instances = []
        for reservation in response.get('Reservations', []):
            instances.extend(reservation.get('Instances', []))
        return instances