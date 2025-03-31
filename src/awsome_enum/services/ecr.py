from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta

class ECRService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'ecr', debug)
        self.public_client = session.client('ecr-public') if session else None
        self.supported_actions = [
            "ecr:*",
            "ecr:DescribeRegistry",
            "ecr:DescribeRepositories",
            "ecr:ListImages",
            "ecr:DescribeImages",
            "ecr:GetRepositoryPolicy",
            "ecr-public:DescribeRepositories"
        ]

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating ECR Resources")
        print_cyan("*" * 80)

        try:
            self._handle_describe_registry("ecr:DescribeRegistry", "*")
            self._handle_describe_repositories("ecr:DescribeRepositories", "*")
            self._handle_describe_public_repositories("ecr-public:DescribeRepositories", "*")
        except Exception as e:
            print_red(f"Error enumerating ECR resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        if action in ("ecr:DescribeRegistry", "ecr:*"):
            self._handle_describe_registry(action, resource)
        elif action in ("ecr:DescribeRepositories", "ecr:*"):
            self._handle_describe_repositories(action, resource)
        elif action in ("ecr:ListImages", "ecr:*"):
            self._handle_list_images(action, resource)
        elif action in ("ecr:GetRepositoryPolicy", "ecr:*"):
            self._handle_get_repository_policy(action, resource)
        elif action in ("ecr-public:DescribeRepositories", "ecr:*"):
            self._handle_describe_public_repositories(action, resource)

    def _handle_describe_registry(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Checking registry details")
        try:
            registry = self.describe_registry()
            if registry:
                registry_data = [
                    ['Registry ID', registry.get('registryId')],
                    ['Replication Configuration', str(registry.get('replicationConfiguration', {}))]
                ]
                print(tabulate(registry_data, headers=['Property', 'Value'], tablefmt='simple'))

                # Get registry policy
                policy = self.get_registry_policy()
                if policy:
                    print_yellow("\nRegistry Policy:")
                    print(policy)
        except Exception as e:
            if self.debug:
                print_red(f"Error in registry handler: {str(e)}")

    def _handle_describe_repositories(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing repositories")
        try:
            repositories = self.describe_repositories()
            if repositories:
                for repo in repositories:
                    print_yellow(f"\n[*] Repository: {repo.get('repositoryName')}")
                    repo_data = [
                        ['ARN', repo.get('repositoryArn')],
                        ['URI', repo.get('repositoryUri')],
                        ['Created', repo.get('createdAt')],
                        ['Image Tags Mutability', repo.get('imageTagMutability')],
                        ['Encryption Type', repo.get('encryptionConfiguration', {}).get('encryptionType', 'N/A')]
                    ]
                    print(tabulate(repo_data, tablefmt='simple'))
            else:
                print_yellow("No repositories found.")
        except Exception as e:
            if self.debug:
                print_red(f"Error in repositories handler: {str(e)}")

    def _handle_list_images(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing images")
        try:
            if resource == '*':
                repositories = self.describe_repositories()
                for repo in repositories:
                    repo_name = repo.get('repositoryName')
                    self._display_images(repo_name)
            else:
                repo_name = resource.split('/')[-1]
                self._display_images(repo_name)
        except Exception as e:
            if self.debug:
                print_red(f"Error in images handler: {str(e)}")

    def _display_images(self, repo_name):
        images = self.list_images(repo_name)
        if images:
            print_yellow(f"\nImages in {repo_name}:")
            for image in images:
                if image:
                    image_data = [
                        ['Digest', image.get('imageDigest', 'N/A')],
                        ['Tag', image.get('imageTag', [])]
                    ]
                    print(tabulate(image_data, tablefmt='simple'))

    def _handle_get_repository_policy(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Getting repository policies")
        try:
            if resource == '*':
                repositories = self.describe_repositories()
                for repo in repositories:
                    repo_name = repo.get('repositoryName')
                    policy = self.get_repository_policy(repo_name)
                    if policy:
                        print_yellow(f"\nPolicy for repository {repo_name}:")
                        print(policy)
            else:
                repo_name = resource.split('/')[-1]
                policy = self.get_repository_policy(repo_name)
                if policy:
                    print_yellow(f"\nPolicy for repository {repo_name}:")
                    print(policy)
        except Exception as e:
            if self.debug:
                print_red(f"Error in policy handler: {str(e)}")

    def _handle_describe_public_repositories(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Checking public repositories")
        try:
            public_repos = self.describe_public_repositories()
            if public_repos:
                print_yellow("\nPublic Repositories:")
                for repo in public_repos:
                    repo_data = [
                        ['Name', repo.get('repositoryName')],
                        ['URI', repo.get('repositoryUri')],
                        ['ARN', repo.get('repositoryArn')]
                    ]
                    print(tabulate(repo_data, tablefmt='simple'))
            else:
                print_yellow("No public repositories found.")
        except Exception as e:
            if self.debug:
                print_red(f"Error in public repositories handler: {str(e)}")

    # API wrapper methods
    def describe_registry(self):
        response = self.client.describe_registry()
        return response

    def describe_repositories(self):
        response = self.client.describe_repositories()
        return response.get('repositories', [])

    def describe_public_repositories(self):
        if self.public_client:
            response = self.public_client.describe_repositories()
            return response.get('repositories', [])
        return []

    def list_images(self, repository_name):
        response = self.client.list_images(repositoryName=repository_name)
        return response.get('imageIds', [])

    def describe_images(self, repository_name, image_digest):
        response = self.client.describe_images(
            repositoryName=repository_name,
            imageIds=[{'imageDigest': image_digest}]
        )
        return response.get('imageDetails', [])[0] if response.get('imageDetails') else None

    def get_registry_policy(self):
        try:
            response = self.client.get_registry_policy()
            return response.get('policyText')
        except ClientError:
            return None

    def get_repository_policy(self, repository_name):
        try:
            response = self.client.get_repository_policy(repositoryName=repository_name)
            return response.get('policyText')
        except ClientError:
            return None