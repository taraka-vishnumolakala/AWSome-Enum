import yaml
import json
from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from ..utils import print_cyan, print_yellow, print_green, print_red, print_magenta

class IAMService(AWSServiceInterface):
    """Implementation of AWS IAM service enumeration and exploitation."""
    
    def __init__(self, session=None, debug=False):
        super().__init__(session=session, service_name='iam', debug=debug)
        self.sts = self.session.client('sts')
        self.available_services = None
        self.all_resource_actions = {}
        self.supported_actions = [
            "iam:ListRoles", "iam:ListUsers", "iam:GetPolicyVersion", "iam:*"
        ]

    def enumerate(self):
        return self._enumerate_permissions()
    
    def handle_permission_action(self, action, resource):
        if action in ("iam:ListRoles", "iam:*"):
            print_yellow("\n[*] Found iam:ListRoles permission - Listing all roles:\n")
            try:
                roles = self.list_roles()
                if roles:
                    role_data = [[role['RoleName'], role['Arn']] for role in roles]
                    print(tabulate(role_data, headers=['Role Name', 'ARN'], tablefmt='plain'))
                    print_magenta("\n💡 Tip: Use 'awsome-enum --profile [profile] find-roles [role-name]' to enumerate permissions for specific roles")
                else:
                    print_yellow("  No roles found.")
            except Exception as e:
                print_red(f"Error listing roles: {str(e)}")

        elif action in ("iam:ListUsers", "iam:*"):
            print_yellow("\n[*] Found iam:ListUsers permission - Listing all users:\n")
            try:
                users = self.client.list_users()['Users']
                if users:
                    user_data = [[user['UserName'], user['Arn']] for user in users]
                    print(tabulate(user_data, headers=['User Name', 'ARN'], tablefmt='plain'))
                else:
                    print_yellow("  No users found.")
            except Exception as e:
                print_red(f"Error listing users: {str(e)}")

        elif action in ("iam:GetPolicyVersion", "iam:*"):
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
    
    def set_available_services(self, services_dict):
        self.available_services = services_dict
    
    def _enumerate_permissions(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating IAM Resources and Permissions")
        print_cyan("*" * 80)

        self.all_resource_actions = {}

        identity = self.get_caller_identity()
        principal_type = self._determine_principal_type(identity)

        self._display_principal_info(identity, principal_type)

        policies = self._fetch_principal_policies(identity, principal_type)
        attached_policies = policies['attached_policies']
        inline_policies = policies['inline_policies']
        principal_name = policies['principal_name']
        
        print_cyan(f"\n[*] Attached {principal_type.title()} Policies:\n")
        print(yaml.dump(attached_policies))
        
        print_cyan(f"\n[*] Inline {principal_type.title()} Policies:\n")
        print(yaml.dump(inline_policies))

        self._process_attached_policies(attached_policies)
        self._process_inline_policies(inline_policies, principal_type, principal_name)

        self._execute_deep_enumeration()

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
        
    def _fetch_principal_policies(self, identity, principal_type):
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
            self._parse_policy_document(policy_document)

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
        else:
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

    def _parse_policy_document(self, policy_document):
        resource_actions = self.parse_policy_document(policy_document)
        
        for resource, actions in resource_actions.items():
            if resource not in self.all_resource_actions:
                self.all_resource_actions[resource] = []
            for action in actions:
                if action not in self.all_resource_actions[resource]:
                    self.all_resource_actions[resource].append(action)
    
    def _execute_deep_enumeration(self):
        if not self.all_resource_actions:
            print_yellow("\n[*] No permissions found to enumerate.")
            return
            
        print_cyan("\n" + "*" * 80)
        print_cyan(f"Found {len(self.all_resource_actions)} resources with permissions")
        print_cyan("*" * 80)
        
        for i, (resource, actions) in enumerate(self.all_resource_actions.items()):
            print_yellow(f"\n[{i+1}] Resource: {resource}")
            print_yellow(f"    Actions: {', '.join(sorted(actions))}")
        
        print_magenta("\nWould you like to perform detailed enumeration of all permissions in the identified policies? (y/n): ")
        user_choice = input().strip().lower()

        if user_choice == 'y' or user_choice == 'yes':
            # print(yaml.dump(self.all_resource_actions))
            for resource, actions in self.all_resource_actions.items():
                is_wildcard = '*' in resource
                for action in actions:
                    self._enumerate_and_list_resources(action, resource, is_wildcard)
        else:
            print_red("\nDetailed permission enumeration cancelled. Thank you for using AWSome-enum.")
            return

    def _enumerate_and_list_resources(self, action, resource, is_resource_wildcard=False):
        service_prefix = action.split(':')[0] if ':' in action else None
        
        if not service_prefix:
            return

        if is_resource_wildcard:
            print("\n" + "-" * 100)
            print_green(f"\n⚠️  Resource is a wildcard (*) for action: {action}")

        if self.available_services and service_prefix in self.available_services:
            service = self.available_services[service_prefix]
            if action in service.supported_actions:
                if not is_resource_wildcard:
                    print("\n" + "-" * 100)
                
                print_yellow(f"\n[*] Enumerating permissions for action: {action} on resource: {resource}")
                service.handle_permission_action(action, resource)
            else: 
                if not is_resource_wildcard and self.debug:
                    print("\n" + "-" * 100)
                    self.handle_unimplemented_action(action, resource)

        self.check_interesting_permissions(action, resource)

    # subcommand methods
    def find_roles(self, role_patterns):
        print_cyan("\n" + "=" * 80)
        print_cyan("Searching for Specific Roles")
        print_cyan("=" * 80)

        print_cyan("\n[*] Searching for roles matching the provided patterns:\n")

        try:
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
        except Exception as e:
            print_red(f"Error finding roles: {str(e)}")

    # Wrapper methods for IAM API calls
    def get_caller_identity(self):
        return self.sts.get_caller_identity()
    
    def list_roles(self):
        response = self.client.list_roles()
        roles = response['Roles']
        
        # Handle pagination
        while response.get('IsTruncated', False):
            marker = response['Marker']
            response = self.client.list_roles(Marker=marker)
            roles.extend(response['Roles'])
            
        return roles
    
    def list_attached_user_policies(self, user_name):
        response = self.client.list_attached_user_policies(UserName=user_name)
        policies = response['AttachedPolicies']
        
        # Handle pagination
        while response.get('IsTruncated', False):
            marker = response['Marker']
            response = self.client.list_attached_user_policies(UserName=user_name, Marker=marker)
            policies.extend(response['AttachedPolicies'])
            
        return policies
    
    def list_attached_role_policies(self, role_name):
        response = self.client.list_attached_role_policies(RoleName=role_name)
        policies = response['AttachedPolicies']
        
        # Handle pagination
        while response.get('IsTruncated', False):
            marker = response['Marker']
            response = self.client.list_attached_role_policies(RoleName=role_name, Marker=marker)
            policies.extend(response['AttachedPolicies'])
            
        return policies
    
    def list_user_policies(self, user_name):
        response = self.client.list_user_policies(UserName=user_name)
        policies = response['PolicyNames']
        
        # Handle pagination
        while response.get('IsTruncated', False):
            marker = response['Marker']
            response = self.client.list_user_policies(UserName=user_name, Marker=marker)
            policies.extend(response['PolicyNames'])
            
        return policies
    
    def list_role_policies(self, role_name):
        response = self.client.list_role_policies(RoleName=role_name)
        policies = response['PolicyNames']
        
        # Handle pagination
        while response.get('IsTruncated', False):
            marker = response['Marker']
            response = self.client.list_role_policies(RoleName=role_name, Marker=marker)
            policies.extend(response['PolicyNames'])
            
        return policies
    
    def get_policy(self, policy_arn):
        return self.client.get_policy(PolicyArn=policy_arn)['Policy']
    
    def get_policy_version(self, policy_arn, version_id):
        return self.client.get_policy_version(PolicyArn=policy_arn, VersionId=version_id)['PolicyVersion']
    
    def get_user_policy(self, user_name, policy_name):
        return self.client.get_user_policy(UserName=user_name, PolicyName=policy_name)['PolicyDocument']
    
    def get_role_policy(self, role_name, policy_name):
        return self.client.get_role_policy(RoleName=role_name, PolicyName=policy_name)['PolicyDocument']