from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta
import boto3

class CognitoService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'cognito-identity', debug)
        self.idp_client = session.client('cognito-idp') if session else boto3.client('cognito-idp')
        self.supported_actions = [
            "cognito-identity:*",
            "cognito-identity:ListIdentityPools",
            "cognito-identity:DescribeIdentityPool",
            "cognito-identity:ListIdentities",
            "cognito-identity:GetIdentityPoolRoles",
            "cognito-idp:ListUserPools",
            "cognito-idp:ListUsers",
            "cognito-idp:ListGroups",
            "cognito-idp:ListUsersInGroup",
            "cognito-idp:ListUserPoolClients",
            "cognito-idp:ListIdentityProviders",
            "cognito-idp:ListUserImportJobs",
            "cognito-idp:GetUserPoolMfaConfig",
            "cognito-idp:DescribeRiskConfiguration"
        ]

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating Cognito Resources")
        print_cyan("*" * 80)

        try:
            self._handle_list_identity_pools("cognito-identity:ListIdentityPools", "*")
            self._handle_list_user_pools("cognito-idp:ListUserPools", "*")
        except Exception as e:
            print_red(f"Error enumerating Cognito resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        if "cognito-identity:ListIdentityPools" in action or "cognito-identity:List*" in action or "cognito-identity:*" in action:
            self._handle_list_identity_pools(action, resource)
        elif "cognito-identity:DescribeIdentityPool" in action or "cognito-identity:Describe*" in action or "cognito-identity:*" in action:
            self._handle_describe_identity_pool(action, resource)
        elif "cognito-identity:ListIdentities" in action or "cognito-identity:List*" in action or "cognito-identity:*" in action:
            self._handle_list_identities(action, resource)
        elif "cognito-identity:GetIdentityPoolRoles" in action or "cognito-identity:Get*" in action or "cognito-identity:*" in action:
            self._handle_get_identity_pool_roles(action, resource)
        elif "cognito-idp:ListUserPools" in action or "cognito-idp:List*" in action or "cognito-idp:*" in action:
            self._handle_list_user_pools(action, resource)
        elif "cognito-idp:ListUsers" in action or "cognito-idp:List*" in action or "cognito-idp:*" in action:
            self._handle_list_users(action, resource)
        elif "cognito-idp:ListGroups" in action or "cognito-idp:List*" in action or "cognito-idp:*" in action:
            self._handle_list_groups(action, resource)
        elif "cognito-idp:ListUsersInGroup" in action or "cognito-idp:List*" in action or "cognito-idp:*" in action:
            self._handle_list_users_in_group(action, resource)
        elif "cognito-idp:ListUserPoolClients" in action or "cognito-idp:List*" in action or "cognito-idp:*" in action:
            self._handle_list_user_pool_clients(action, resource)
        elif "cognito-idp:ListIdentityProviders" in action or "cognito-idp:List*" in action or "cognito-idp:*" in action:
            self._handle_list_identity_providers(action, resource)
        elif "cognito-idp:ListUserImportJobs" in action or "cognito-idp:List*" in action or "cognito-idp:*" in action:
            self._handle_list_user_import_jobs(action, resource)
        elif "cognito-idp:GetUserPoolMfaConfig" in action or "cognito-idp:Get*" in action or "cognito-idp:*" in action:
            self._handle_get_user_pool_mfa_config(action, resource)
        elif "cognito-idp:DescribeRiskConfiguration" in action or "cognito-idp:Describe*" in action or "cognito-idp:*" in action:
            self._handle_describe_risk_configuration(action, resource)

    def _handle_list_identity_pools(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing identity pools")
        try:
            response = self.client.list_identity_pools(MaxResults=60)
            if 'IdentityPools' in response:
                print_green("\nIdentity Pools:")
                for pool in response['IdentityPools']:
                    print_green(f"ID: {pool['IdentityPoolId']}, Name: {pool['IdentityPoolName']}")
                    self._handle_describe_identity_pool(action, pool['IdentityPoolId'])
        except Exception as e:
            if self.debug:
                print_red(f"Error in list identity pools: {str(e)}")

    def _handle_describe_identity_pool(self, action, pool_id):
        print_yellow(f"\n[*] Describing identity pool: {pool_id}")
        try:
            response = self.client.describe_identity_pool(IdentityPoolId=pool_id)
            print_green(tabulate([[k, v] for k, v in response.items()], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error describing identity pool: {str(e)}")

    def _handle_list_identities(self, action, pool_id):
        print_yellow(f"\n[*] Listing identities for pool: {pool_id}")
        try:
            response = self.client.list_identities(
                IdentityPoolId=pool_id,
                MaxResults=60
            )
            if 'Identities' in response:
                print_green(tabulate([[i['IdentityId'], i.get('Logins', [])] 
                    for i in response['Identities']], 
                    headers=['Identity ID', 'Logins'], 
                    tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error listing identities: {str(e)}")

    def _handle_get_identity_pool_roles(self, action, pool_id):
        print_yellow(f"\n[*] Getting roles for identity pool: {pool_id}")
        try:
            response = self.client.get_identity_pool_roles(IdentityPoolId=pool_id)
            if 'Roles' in response:
                print_green(tabulate([[k, v] for k, v in response['Roles'].items()],
                    headers=['Role Type', 'Role ARN'],
                    tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error getting identity pool roles: {str(e)}")

    def _handle_list_user_pools(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing user pools")
        try:
            response = self.idp_client.list_user_pools(MaxResults=60)
            if 'UserPools' in response:
                for pool in response['UserPools']:
                    print_green(f"\nPool ID: {pool['Id']}, Name: {pool['Name']}")
                    self._handle_list_users(action, pool['Id'])
                    self._handle_list_groups(action, pool['Id'])
                    self._handle_list_user_pool_clients(action, pool['Id'])
                    self._handle_list_identity_providers(action, pool['Id'])
                    self._handle_get_user_pool_mfa_config(action, pool['Id'])
                    self._handle_describe_risk_configuration(action, pool['Id'])
        except Exception as e:
            if self.debug:
                print_red(f"Error listing user pools: {str(e)}")

    def _handle_list_users(self, action, pool_id):
        print_yellow(f"\n[*] Listing users for pool: {pool_id}")
        try:
            response = self.idp_client.list_users(UserPoolId=pool_id)
            if 'Users' in response:
                print_green(tabulate([[u['Username'], u.get('UserStatus', 'N/A')] 
                    for u in response['Users']], 
                    headers=['Username', 'Status'],
                    tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error listing users: {str(e)}")

    def _handle_list_groups(self, action, pool_id):
        print_yellow(f"\n[*] Listing groups for pool: {pool_id}")
        try:
            response = self.idp_client.list_groups(UserPoolId=pool_id)
            if 'Groups' in response:
                for group in response['Groups']:
                    print_green(f"\nGroup: {group['GroupName']}")
                    self._handle_list_users_in_group(action, pool_id, group['GroupName'])
        except Exception as e:
            if self.debug:
                print_red(f"Error listing groups: {str(e)}")

    def _handle_list_users_in_group(self, action, pool_id, group_name):
        print_yellow(f"\n[*] Listing users in group: {group_name}")
        try:
            response = self.idp_client.list_users_in_group(
                UserPoolId=pool_id,
                GroupName=group_name
            )
            if 'Users' in response:
                print_green(tabulate([[u['Username'], u.get('UserStatus', 'N/A')] 
                    for u in response['Users']], 
                    headers=['Username', 'Status'],
                    tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error listing users in group: {str(e)}")

    def _handle_list_user_pool_clients(self, action, pool_id):
        print_yellow(f"\n[*] Listing clients for pool: {pool_id}")
        try:
            response = self.idp_client.list_user_pool_clients(UserPoolId=pool_id)
            if 'UserPoolClients' in response:
                print_green(tabulate([[c['ClientId'], c['ClientName']] 
                    for c in response['UserPoolClients']], 
                    headers=['Client ID', 'Client Name'],
                    tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error listing pool clients: {str(e)}")

    def _handle_list_identity_providers(self, action, pool_id):
        print_yellow(f"\n[*] Listing identity providers for pool: {pool_id}")
        try:
            response = self.idp_client.list_identity_providers(UserPoolId=pool_id)
            if 'Providers' in response:
                print_green(tabulate([[p['ProviderName'], p['ProviderType']] 
                    for p in response['Providers']], 
                    headers=['Provider Name', 'Provider Type'],
                    tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error listing identity providers: {str(e)}")

    def _handle_list_user_import_jobs(self, action, pool_id):
        print_yellow(f"\n[*] Listing user import jobs for pool: {pool_id}")
        try:
            response = self.idp_client.list_user_import_jobs(
                UserPoolId=pool_id,
                MaxResults=60
            )
            if 'UserImportJobs' in response:
                print_green(tabulate([[j['JobName'], j['Status']] 
                    for j in response['UserImportJobs']], 
                    headers=['Job Name', 'Status'],
                    tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error listing import jobs: {str(e)}")

    def _handle_get_user_pool_mfa_config(self, action, pool_id):
        print_yellow(f"\n[*] Getting MFA config for pool: {pool_id}")
        try:
            response = self.idp_client.get_user_pool_mfa_config(UserPoolId=pool_id)
            print_green(tabulate([[k, str(v)] for k, v in response.items() if k != 'ResponseMetadata'],
                tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error getting MFA config: {str(e)}")

    def _handle_describe_risk_configuration(self, action, pool_id):
        print_yellow(f"\n[*] Getting risk configuration for pool: {pool_id}")
        try:
            response = self.idp_client.describe_risk_configuration(UserPoolId=pool_id)
            if 'RiskConfiguration' in response:
                print_green(tabulate([[k, str(v)] for k, v in response['RiskConfiguration'].items()],
                    tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error describing risk configuration: {str(e)}")
