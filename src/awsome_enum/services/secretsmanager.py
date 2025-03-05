import yaml
from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta

class SecretsManagerService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'secretsmanager', debug)
        self.supported_actions = ["secretsmanager:ListSecrets", "secretsmanager:GetResourcePolicy", "secretsmanager:PutResourcePolicy", "secretsmanager:*"]
    
    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating Secrets Manager Resources")
        print_cyan("*" * 80)
        
        try:
            self._list_and_check_secrets()
        except Exception as e:
            print_red(f"Error enumerating Secrets Manager resources: {str(e)}")
    
    def handle_permission_action(self, action, resource):
        if "secretsmanager:ListSecrets" in action or "secretsmanager:*" in action:
            print_yellow("\n[*] Found secretsmanager:ListSecrets permission - Listing all secrets:")
            self._list_and_check_secrets()
        elif "secretsmanager:GetResourcePolicy" in action or "secretsmanager:*" in action:
            self._check_secret_policy(resource)
        elif "secretsmanager:PutResourcePolicy" in action or "secretsmanager:*" in action:
            print_magenta(f"\n💡 Found 'secretsmanager:PutResourcePolicy' on resource '{resource}'.")
            print_magenta("Try using 'aws secretsmanager put-resource-policy --secret-id <secret_name> --resource-policy file:///tmp/policy.json'.")

    def _list_and_check_secrets(self):
        try:
            secrets = self.list_secrets()
            if not secrets:
                print_yellow("No secrets found.")
                return
            
            secret_data = [[secret['Name'], secret.get('ARN', 'N/A')] for secret in secrets]
            print_cyan("\n[*] Secrets Found:\n")
            print(tabulate(secret_data, headers=['Secret Name', 'ARN'], tablefmt='plain'))
            
        except Exception as e:
            print_red(f"Error listing secrets: {str(e)}")

    def _check_secret_policy(self, resource):
        try:
            print_yellow(f"\n[*] Found secretsmanager:GetResourcePolicy permissions on '{resource}'. Listing policy details:\n")
            policy = self.get_resource_policy(secret_id=resource)
            filtered_policy = {
                'Name': policy['Name'],
                'ARN': policy['ARN']
            }
            print(yaml.dump(filtered_policy))
        except Exception as e:
            print_red(f"Error fetching resource policy: {str(e)}")

    # Wrapper methods for Secrets Manager API calls
    def list_secrets(self):
        """List all secrets in the account."""
        response = self.client.list_secrets()
        return response.get('SecretList', [])
    
    def get_resource_policy(self, secret_id):
        """Get resource policy for a specific secret."""
        response = self.client.get_resource_policy(
            SecretId=secret_id
        )
        return response