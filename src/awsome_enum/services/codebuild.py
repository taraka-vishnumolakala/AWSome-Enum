from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta
import boto3

class CodeBuildService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'codebuild', debug)
        self.supported_actions = [
            "codebuild:*",
            "codebuild:List*",
            "codebuild:BatchGet*",
            "codebuild:Describe*",
            "codebuild:ListSourceCredentials",
            "codebuild:ListSharedProjects",
            "codebuild:ListProjects",
            "codebuild:BatchGetProjects",
            "codebuild:ListBuilds",
            "codebuild:ListBuildsForProject",
            "codebuild:ListBuildBatches",
            "codebuild:ListBuildBatchesForProject",
            "codebuild:ListReports",
            "codebuild:DescribeTestCases"
        ]

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating CodeBuild Resources")
        print_cyan("*" * 80)

        try:
            self._handle_list_source_credentials("codebuild:ListSourceCredentials", "*")
            self._handle_list_projects("codebuild:ListProjects", "*")
            self._handle_list_shared_projects("codebuild:ListSharedProjects", "*")
            self._handle_list_builds("codebuild:ListBuilds", "*")
            self._handle_list_build_batches("codebuild:ListBuildBatches", "*")
            self._handle_list_reports("codebuild:ListReports", "*")
            self._handle_list_builds_for_project("codebuild:ListBuildsForProject", "*")
            self._handle_list_build_batches_for_project("codebuild:ListBuildBatchesForProject", "*")
            self._handle_batch_get_projects("codebuild:BatchGetProjects", "*")
            self._handle_describe_test_cases("codebuild:DescribeTestCases", "*")
        except Exception as e:
            print_red(f"Error enumerating CodeBuild resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        if "codebuild:ListSourceCredentials" in action or "codebuild:List*" in action or "codebuild:*" in action:
            self._handle_list_source_credentials(action, resource)
        elif "codebuild:ListSharedProjects" in action or "codebuild:List*" in action or "codebuild:*" in action:
            self._handle_list_shared_projects(action, resource)
        elif "codebuild:ListProjects" in action or "codebuild:List*" in action or "codebuild:*" in action:
            self._handle_list_projects(action, resource)
        elif "codebuild:ListBuilds" in action or "codebuild:List*" in action or "codebuild:*" in action:
            self._handle_list_builds(action, resource)
        elif "codebuild:ListBuildsForProject" in action or "codebuild:List*" in action or "codebuild:*" in action:
            self._handle_list_builds_for_project(action, resource)
        elif "codebuild:ListBuildBatches" in action or "codebuild:List*" in action or "codebuild:*" in action:
            self._handle_list_build_batches(action, resource)
        elif "codebuild:ListBuildBatchesForProject" in action or "codebuild:List*" in action or "codebuild:*" in action:
            self._handle_list_build_batches_for_project(action, resource)
        elif "codebuild:ListReports" in action or "codebuild:List*" in action or "codebuild:*" in action:
            self._handle_list_reports(action, resource)
        elif "codebuild:BatchGetProjects" in action or "codebuild:BatchGet*" in action or "codebuild:*" in action:
            self._handle_batch_get_projects(action, resource)
        elif "codebuild:DescribeTestCases" in action or "codebuild:Describe*" in action or "codebuild:*" in action:
            self._handle_describe_test_cases(action, resource)

    def _handle_list_source_credentials(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing source credentials")
        try:
            creds = self.list_source_credentials()
            if creds:
                print_yellow("\nSource Credentials:")
                creds_data = [[
                    cred.get('arn'),
                    cred.get('serverType'),
                    cred.get('authType')
                ] for cred in creds]
                print(tabulate(creds_data, headers=['ARN', 'Server Type', 'Auth Type'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in source credentials handler: {str(e)}")

    def _handle_list_projects(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing projects")
        try:
            projects = self.list_projects()
            if projects:
                print_yellow("\nProjects:")
                for project in projects:
                    print_green(f"\nProject: {project}")
                    # Get detailed project info
                    project_details = self.batch_get_projects([project])
                    if project_details:
                        for detail in project_details:
                            env = detail.get('environment', {})
                            print_yellow("\nEnvironment Variables:")
                            if env.get('environmentVariables'):
                                env_vars = [[var['name'], var['value']] for var in env['environmentVariables']]
                                print(tabulate(env_vars, headers=['Name', 'Value'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in projects handler: {str(e)}")

    def _handle_list_shared_projects(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing shared projects")
        try:
            shared_projects = self.list_shared_projects()
            if shared_projects:
                print_yellow("\nShared Projects:")
                for project in shared_projects:
                    print_green(project)
        except Exception as e:
            if self.debug:
                print_red(f"Error in shared projects handler: {str(e)}")

    def _handle_list_builds(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing builds")
        try:
            builds = self.list_builds()
            if builds:
                print_yellow("\nBuilds:")
                print(tabulate([[build] for build in builds], headers=['Build ID'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in builds handler: {str(e)}")

    def _handle_list_builds_for_project(self, action, project_name):
        print_yellow(f"\n[*] Found {action} permission - Listing builds for project {project_name}")
        try:
            builds = self.list_builds_for_project(project_name)
            if builds:
                print_yellow(f"\nBuilds for project {project_name}:")
                print(tabulate([[build] for build in builds], headers=['Build ID'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in project builds handler: {str(e)}")

    def _handle_list_build_batches(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing build batches")
        try:
            batches = self.list_build_batches()
            if batches:
                print_yellow("\nBuild Batches:")
                print(tabulate([[batch] for batch in batches], headers=['Batch ID'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in build batches handler: {str(e)}")

    def _handle_list_build_batches_for_project(self, action, project_name):
        print_yellow(f"\n[*] Found {action} permission - Listing build batches for project {project_name}")
        try:
            batches = self.list_build_batches_for_project(project_name)
            if batches:
                print_yellow(f"\nBuild Batches for project {project_name}:")
                print(tabulate([[batch] for batch in batches], headers=['Batch ID'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in project build batches handler: {str(e)}")

    def _handle_list_reports(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing reports")
        try:
            reports = self.list_reports()
            if reports:
                print_yellow("\nReports:")
                for report in reports:
                    print_green(f"\nReport ARN: {report}")
                    self._handle_describe_test_cases(action, report)
        except Exception as e:
            if self.debug:
                print_red(f"Error in reports handler: {str(e)}")

    def _handle_describe_test_cases(self, action, report_arn):
        try:
            test_cases = self.describe_test_cases(report_arn)
            if test_cases:
                print_yellow("\nTest Cases:")
                test_data = [[
                    case.get('testName'),
                    case.get('status'),
                    case.get('duration')
                ] for case in test_cases]
                print(tabulate(test_data, headers=['Test Name', 'Status', 'Duration'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in test cases handler: {str(e)}")

    def _handle_batch_get_projects(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Getting project details")
        try:
            projects = self.list_projects()
            if projects:
                project_details = self.batch_get_projects(projects)
                if project_details:
                    print_yellow("\nProject Details:")
                    for detail in project_details:
                        print_green(f"\nProject Name: {detail.get('name')}")
                        print_yellow(f"Description: {detail.get('description')}")
                        print_yellow(f"Source Type: {detail.get('source', {}).get('type')}")
        except Exception as e:
            if self.debug:
                print_red(f"Error in batch get projects handler: {str(e)}")

    # API wrapper methods
    def list_source_credentials(self):
        response = self.client.list_source_credentials()
        return response.get('sourceCredentialsInfos', [])

    def list_projects(self):
        response = self.client.list_projects()
        return response.get('projects', [])

    def list_shared_projects(self):
        response = self.client.list_shared_projects()
        return response.get('projects', [])

    def batch_get_projects(self, names):
        response = self.client.batch_get_projects(names=names)
        return response.get('projects', [])

    def list_builds(self):
        response = self.client.list_builds()
        return response.get('ids', [])

    def list_builds_for_project(self, project_name):
        response = self.client.list_builds_for_project(projectName=project_name)
        return response.get('ids', [])

    def list_build_batches(self):
        response = self.client.list_build_batches()
        return response.get('ids', [])

    def list_build_batches_for_project(self, project_name):
        response = self.client.list_build_batches_for_project(projectName=project_name)
        return response.get('ids', [])

    def list_reports(self):
        response = self.client.list_reports()
        return response.get('reports', [])

    def describe_test_cases(self, report_arn):
        response = self.client.describe_test_cases(reportArn=report_arn)
        return response.get('testCases', [])
