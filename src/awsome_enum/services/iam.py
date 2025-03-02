import yaml
from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from ..utils import load_permissions, print_cyan, print_yellow, print_green, print_red, print_magenta

class IAMService(AWSServiceInterface):
    """Implementation of AWS IAM service enumeration and exploitation."""
    
    def __init__(self, session=None):
        super().__init__(session, 'iam')
        self.sts = self.session.client('sts')
        self.interesting_permissions = load_permissions()
        self.available_services = None  # Will be set from outside

    def enumerate(self):
        """Public method for main enumerator to call."""
        return self._enumerate_permissions()
    
    def set_available_services(self, services_dict):
        """Set available services dictionary from the main enumerator."""
        self.available_services = services_dict
    
    def _enumerate_permissions(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating IAM Resources and Permissions")
        print_cyan("*" * 80)

        identity = self.get_caller_identity()
        principal_type = self._determine_principal_type(identity)

        self._display_principal_info(identity, principal_type)

        policies = self.fetch_principal_policies(identity, principal_type)
        attached_policies = policies['attached_policies']
        inline_policies = policies['inline_policies']
        principal_name = policies['principal_name']
        
        print_cyan(f"\n[*] Attached {principal_type.title()} Policies:\n")
        print(yaml.dump(attached_policies))
        
        print_cyan(f"\n[*] Inline {principal_type.title()} Policies:\n")
        print(yaml.dump(inline_policies))

        self._process_attached_policies(attached_policies)
        self._process_inline_policies(inline_policies, principal_type, principal_name)

    def check_interesting_permissions(self, policy_document):
        resource_actions = self._parse_policy_document(policy_document)
        
        for resource, actions in resource_actions.items():
            for action in actions:
                is_resource_wildcard = resource == '*'
                
                if action in self.interesting_permissions:
                    print_green(f"\n🔍 Found potentially interesting permission: {action}")
                    
                self.enumerate_and_list_resources(action, resource, is_resource_wildcard)
                    
    def get_caller_identity(self):
        return self.sts.get_caller_identity()

    def _determine_principal_type(self, identity):
        return 'user' if 'user/' in identity.get('Arn', '') else 'role'
    
    def _display_principal_info(self, identity, principal_type):
        print_cyan(f"\n[*] Fetching {principal_type} information:\n")
        principal_info = self._extract_principal_info(identity, principal_type)
        print(yaml.dump(principal_info, default_flow_style=False))

    def _extract_principal_info(self, identity, principal_type):
        if principal_type == 'user':
            user_name = identity["Arn"].split('/')[-1]
            return {
                "UserId": identity["UserId"],
                "Account": identity["Account"],
                "Arn": identity["Arn"],
                "UserName": user_name
            }
        else:
            role_arn = identity["Arn"]
            role_name = role_arn.split('/')[-2] if 'assumed-role' in role_arn else role_arn.split('/')[-1]
            return {
                "RoleId": identity["UserId"],
                "Account": identity["Account"],
                "Arn": identity["Arn"],
                "RoleName": role_name
            }
        
    def fetch_principal_policies(self, identity, principal_type):
        try:
            result = {
                'attached_policies': [],
                'inline_policies': [],
                'principal_name': None
            }

            if principal_type == 'user':
                user_name = identity["Arn"].split('/')[-1]
                result['attached_policies'] = self.list_attached_user_policies(user_name)
                result['inline_policies'] = self.list_user_policies(user_name)
                result['principal_name'] = user_name
            else:
                role_arn = identity["Arn"]
                role_name = role_arn.split('/')[-2] if 'assumed-role' in role_arn else role_arn.split('/')[-1]
                result['attached_policies'] = self.list_attached_role_policies(role_name)
                result['inline_policies'] = self.list_role_policies(role_name)
                result['principal_name'] = role_name

            return result
        
        except Exception as e:
            print_red(f"  [!] Failed to get policies for {principal_type}: {str(e)}")
            return {
                'attached_policies': [],
                'inline_policies': [],
                'principal_name': None
            }
        
    def _process_attached_policies(self, attached_policies):
        for policy in attached_policies:
            print_yellow(f"\n[*] Processing Attached Policy: {policy['PolicyArn']}\n")
            self._fetch_policy_details(policy_arn=policy['PolicyArn'])

    def _process_inline_policies(self, inline_policies, principal_type, principal_name):
        for policy_name in inline_policies:
            print_yellow(f"\n[*] Processing Inline Policy: {policy_name}\n")
            self._fetch_policy_details(
                is_inline=True,
                principal_type=principal_type,
                name=principal_name,
                policy_name=policy_name
            )

    def _fetch_policy_details(self, is_inline=False, policy_arn=None, principal_type=None, name=None, policy_name=None):
        try:
            policy_document = self._get_policy_document(
                is_inline, 
                policy_arn, 
                principal_type, 
                name, 
                policy_name
            )

            self._display_policy_document(policy_document)
            self.check_interesting_permissions(policy_document)

        except Exception as e:
            print_red(f"  [!] Failed to retrieve policy details: {str(e)}")

    def _get_policy_document(self, is_inline, policy_arn, principal_type, name, policy_name):
        if is_inline:
            return self._get_inline_policy_document(principal_type, name, policy_name)
        else:
            return self._get_managed_policy_document(policy_arn)
        
    def _get_inline_policy_document(self, principal_type, name, policy_name):
        if principal_type == 'role':
            return self.get_role_policy(
                role_name=name,
                policy_name=policy_name
            )
        else:  # user
            return self.get_user_policy(
                user_name=name,
                policy_name=policy_name
            )

    def _get_managed_policy_document(self, policy_arn):
        policy = self.get_policy(policy_arn=policy_arn)
        policy_version = self.get_policy_version(
            policy_arn=policy_arn,
            version_id=policy['DefaultVersionId']
        )
        return policy_version['Document']
    
    def _display_policy_document(self, policy_document):
        print(yaml.dump(policy_document))
        print("\n" + "-" * 100)

    def _parse_policy_document(self, policy_document):
        resource_actions = {}

        for statement in policy_document.get('Statement', []):
            # Skip DENY statements
            if statement.get('Effect', '').lower() == 'deny':
                print("\n" + "-" * 100)
                print_red(f"\n⛔ Skipping enumeration - Effect is DENY")
                continue

            # Skip statements with conditions
            if statement.get('Condition'):
                print("\n" + "-" * 100)
                print_red(f"\n🔍 Conditions exist on this policy. Manual intervention needed.")
                print(yaml.dump(statement))
                continue

            # Get actions (handle both string and list)
            actions = statement.get('Action', [])
            if isinstance(actions, str):
                actions = [actions]

            # Get resources (handle both string and list)
            resources = statement.get('Resource', [])
            if isinstance(resources, str):
                resources = [resources]

            # Add actions to each resource
            for resource in resources:
                if resource not in resource_actions:
                    resource_actions[resource] = []
                resource_actions[resource].extend(actions)

        # Remove duplicates from action lists
        for resource in resource_actions:
            resource_actions[resource] = list(set(resource_actions[resource]))

        return resource_actions

    def enumerate_and_list_resources(self, action, resource, is_resource_wildcard=False):
        """
        Centralized method to handle enumeration of resources based on discovered permissions.
        This method will analyze the action and delegate to the appropriate service for enumeration.
        """
        # Skip if no interesting permissions found
        if action not in self.interesting_permissions and not self._is_enumeration_action(action):
            return
        
        # Warn about wildcard resources
        if is_resource_wildcard:
            print_green(f"\n⚠️  Resource is a wildcard (*) for action: {action}")
        
        # Handle IAM service enumeration
        self._handle_iam_enumeration(action, resource)
        
        # Handle other services based on action prefix
        service_prefix = action.split(':')[0] if ':' in action else None
        
        if not service_prefix:
            return
            
        # Trigger enumeration for other services if available
        if service_prefix != 'iam' and self.available_services and service_prefix in self.available_services:
            print_yellow(f"\n[*] Found {service_prefix} permissions - Delegating to {service_prefix.upper()} service")
            service = self.available_services[service_prefix](self.session)
            
            # If the service implements a method to handle specific actions, call it
            if hasattr(service, 'handle_permission_action'):
                service.handle_permission_action(action, resource, is_resource_wildcard)
            # Otherwise just enumerate the service
            else:
                service.enumerate()

    def _is_enumeration_action(self, action):
        """Check if this is an enumeration action."""
        enumeration_actions = [
            'iam:List*', 'iam:Get*', 'iam:*',
            's3:List*', 's3:Get*', 's3:*',
            'secretsmanager:List*', 'secretsmanager:Get*', 'secretsmanager:*',
            'kms:List*', 'kms:Get*', 'kms:*',
            # Add more enumeration patterns for other services
        ]
        
        for pattern in enumeration_actions:
            if pattern.endswith('*'):
                prefix = pattern[:-1]
                if action.startswith(prefix):
                    return True
            elif action == pattern:
                return True
                
        return False
        
    def _handle_iam_enumeration(self, action, resource):
        """Handle IAM-specific enumeration actions."""
        # List Roles
        if "iam:ListRoles" in action or "iam:*" in action:
            print_yellow("\n[*] Found iam:ListRoles permission - Listing all roles:\n")
            roles = self.list_roles()
            role_data = [[role['RoleName'], role['Arn']] for role in roles]
            print(tabulate(role_data, headers=['Role Name', 'ARN'], tablefmt='plain'))
            print_magenta("\n💡 Tip: Use 'awsome-enum --profile [profile] list-role [role-name]' to enumerate permissions for specific roles")

        # List Users
        if "iam:ListUsers" in action or "iam:*" in action:
            print_yellow("\n[*] Found iam:ListUsers permission - Listing all users:\n")
            users = self.client.list_users()['Users']
            user_data = [[user['UserName'], user['Arn']] for user in users]
            print(tabulate(user_data, headers=['User Name', 'ARN'], tablefmt='plain'))

        # Get Policy Version
        if "iam:GetPolicyVersion" in action or "iam:*" in action:
            if resource.startswith('arn:aws:iam::'):
                print_yellow(f"\n[*] Found iam:GetPolicyVersion permissions on '{resource}'. Listing policy details:\n")
                try:
                    policy_arn = resource
                    policy = self.get_policy(policy_arn)
                    policy_version = self.get_policy_version(policy_arn, policy['DefaultVersionId'])
                    policy_document = policy_version['Document']
                    print(yaml.dump(policy_document))
                except Exception as e:
                    print_red(f"Error listing policies: {str(e)}")

    def find_roles(self, role_patterns):
        print_cyan("\n" + "=" * 80)
        print_cyan("Searching for Specific Roles")
        print_cyan("=" * 80)

        print_cyan("\n[*] Searching for roles matching the provided patterns:\n")

        roles = self.list_roles()
        found_roles = False

        for pattern in role_patterns:
            print_yellow(f"\n[*] Searching for roles matching: {pattern}\n")
            matching_roles = [role for role in roles if pattern.lower() in role['RoleName'].lower()]

            if matching_roles:
                found_roles = True
                for role in matching_roles:
                    print_green(f"\n [*]Found a matching role {role['RoleName']} with details:\n")
                    print(yaml.dump(role))
            else:
                print_yellow(f"  No roles found matching pattern: {pattern}")

        if not found_roles:
            print_yellow("\nNo matching roles found for any of the provided patterns.")

    # Wrapper methods for IAM API calls
    def list_roles(self):
        return self.client.list_roles()['Roles']
    
    def list_attached_user_policies(self, user_name):
        return self.client.list_attached_user_policies(UserName=user_name)['AttachedPolicies']
    
    def list_attached_role_policies(self, role_name):
        return self.client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
    
    def list_user_policies(self, user_name):
        return self.client.list_user_policies(UserName=user_name)['PolicyNames']
    
    def list_role_policies(self, role_name):
        return self.client.list_role_policies(RoleName=role_name)['PolicyNames']
    
    def get_policy(self, policy_arn):
        return self.client.get_policy(PolicyArn=policy_arn)['Policy']
    
    def get_policy_version(self, policy_arn, version_id):
        return self.client.get_policy_version(PolicyArn=policy_arn, VersionId=version_id)['PolicyVersion']
    
    def get_user_policy(self, user_name, policy_name):
        return self.client.get_user_policy(UserName=user_name, PolicyName=policy_name)['PolicyDocument']
    
    def get_role_policy(self, role_name, policy_name):
        return self.client.get_role_policy(RoleName=role_name, PolicyName=policy_name)['PolicyDocument']