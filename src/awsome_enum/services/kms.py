import json
import yaml
from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from ..utils import print_cyan, print_yellow, print_red, print_green

class KMSService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'kms', debug)
        self.supported_actions = ["kms:ListKeys", "kms:GetKeyPolicy", "kms:*"]
    
    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating KMS Resources")
        print_cyan("*" * 80)
        
        try:
            self._list_and_check_keys()
        except Exception as e:
            print_red(f"Error enumerating KMS resources: {str(e)}")
    
    def handle_permission_action(self, action, resource):
        if "kms:ListKeys" in action or "kms:*" in action:
            print_yellow("\n[*] Found kms:ListKeys permission - Listing all KMS keys:\n")
            self._list_and_check_keys()

    def _list_and_check_keys(self):
        try:
            keys = self.list_keys()
            if not keys:
                print_yellow("No KMS keys found.")
                return
            
            key_data = [[key['KeyId'], key['KeyArn']] for key in keys]
            print_cyan("\n[*] KMS Keys Found:\n")
            print(tabulate(key_data, headers=['Key ID', 'Key ARN'], tablefmt='plain'))
            
            self._check_key_policies(keys)
            
        except Exception as e:
            print_red(f"Error listing keys: {str(e)}")

    def _check_key_policies(self, keys):
        print_yellow("\n[*] Fetching key policies:\n")
        for key in keys:
            try:
                key_policy = self.get_key_policy(key_id=key['KeyId'])
                policy_name = key_policy['PolicyName']
                print_yellow(f"\n[*] Found key policy for Key ID: {key['KeyId']} with Policy Name: {policy_name}")
                policy_document = json.loads(key_policy['Policy'])
                print(yaml.dump(policy_document))
                
                resource_actions = self.parse_policy_document(policy_document)
                for resource, actions in resource_actions.items():
                    for action in actions:
                        self.check_interesting_permissions(action, resource)
                            
            except Exception as e:
                print_red(f"Error fetching key policy for KeyId '{key['KeyId']}': {str(e)}")

    # Wrapper methods for KMS API calls
    def list_keys(self):
        response = self.client.list_keys()
        return response.get('Keys', [])
    
    def get_key_policy(self, key_id):
        response = self.client.get_key_policy(
            KeyId=key_id,
            PolicyName='default'
        )
        return response