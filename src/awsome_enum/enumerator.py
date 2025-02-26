import boto3
import json
import yaml
from botocore.exceptions import ClientError
from tabulate import tabulate
from .utils import load_permissions, print_cyan, print_yellow, print_green, print_red, print_magenta

class AWSEnumerator:
    def __init__(self, profile=None):
        self.session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self.iam = self.session.client('iam')
        self.sts = self.session.client('sts')
        self.secretsmanager = self.session.client('secretsmanager')
        self.interesting_permissions = load_permissions()

    def get_caller_identity(self):
        return self.sts.get_caller_identity()

    def list_attached_user_policies(self, user_name):
        return self.iam.list_attached_user_policies(UserName=user_name)['AttachedPolicies']
    
    def list_attached_role_policies(self, role_name):
        return self.iam.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']

    def list_user_policies(self, user_name):
        return self.iam.list_user_policies(UserName=user_name)['PolicyNames']
    
    def list_role_policies(self, role_name):
        return self.iam.list_role_policies(RoleName=role_name)['PolicyNames']

    def get_policy(self, policy_arn):
        return self.iam.get_policy(PolicyArn=policy_arn)['Policy']

    def get_policy_version(self, policy_arn, version_id):
        return self.iam.get_policy_version(PolicyArn=policy_arn, VersionId=version_id)['PolicyVersion']

    def get_user_policy(self, user_name, policy_name):
        return self.iam.get_user_policy(UserName=user_name, PolicyName=policy_name)['PolicyDocument']
    
    def get_role_policy(self, role_name, policy_name):
        return self.iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)['PolicyDocument']

    def list_roles(self):
        return self.iam.list_roles()['Roles']

    def check_interesting_permissions(self, action, resource):
        if action in self.interesting_permissions:
            print("\n")
            print_green(f"[!] '{action}' is an Interesting Permission for possible privilege escalation.")
            print_green(f"➡️  More info: {self.interesting_permissions[action]}")
            print_green(f"🎯 Resource: {resource}")
            # print("\n" + "-" * 100)

    def enumerate_and_list_resources(self, action, resource, is_resource_wildcard=False):
        actions = ['iam:*', 'iam:ListRoles', 'iam:ListUsers', 'iam:GetPolicyVersion', 'secretsmanager:*', 'secretsmanager:ListSecrets']
        
        if action not in actions:
            return
        
        print("\n" + "-" * 100)

        if is_resource_wildcard:
            print_green(f"\n⚠️  Resource is a wildcard (*) for action: {action}")

        if "iam:ListRoles" in action or "iam:*" in action:
            print_yellow("\n[*] Found iam:ListRoles permission - Listing all roles:\n")
            roles = self.list_roles()
            role_data = [[role['RoleName'], role['Arn']] for role in roles]
            print(tabulate(role_data, headers=['Role Name', 'ARN'], tablefmt='plain'))
            print_magenta("\n💡 Tip: Use 'awsome-enum --profile [profile] list-role [role-name]' to enumerate permissions for specific roles")

        if "iam:ListUsers" in action or "iam:*" in action:
            print_yellow("\n[*] Found iam:ListUsers permission - Listing all users:\n")
            users = self.iam.list_users()['Users']
            user_data = [[user['UserName'], user['Arn']] for user in users]
            print(tabulate(user_data, headers=['User Name', 'ARN'], tablefmt='plain'))

        if "iam:GetPolicyVersion" in action or "iam:*" in action:
            print_yellow(f"\n[*] Found iam:GetPolicyVersion permissions on '{resource}'. Listing policy details:\n")
            try:
                policy_arn = resource
                policy = self.get_policy(policy_arn)
                policy_version = self.get_policy_version(policy_arn, policy['DefaultVersionId'])
                policy_document = policy_version['Document']
                print(yaml.dump(policy_document))
            except Exception as e:
                print_red(f"Error listing policies: {str(e)}")

        if "secretsmanager:ListSecrets" in action or "secretsmanager:*" in action:
            print_yellow("\n[*] Found secretsmanager:ListSecrets permission - Listing all secrets:\n")
            try:
                secrets = self.secretsmanager.list_secrets()['SecretList']
                secret_data = [[secret['Name'], secret.get('ARN', 'N/A')] for secret in secrets]
                print(tabulate(secret_data, headers=['Secret Name', 'ARN'], tablefmt='plain'))
            except Exception as e:
                print_red(f"Error listing secrets: {str(e)}")

    def enumerate_permissions(self, principal_type):
        print_cyan("\n" + "=" * 80)
        print_cyan(f"Enumerating {principal_type.title()} Permissions")
        print_cyan("=" * 80)

        # Fetch principal information
        print_cyan(f"\n[*] Fetching {principal_type} information:\n")
        try:
            if principal_type == 'user':
                principal_info = self.get_caller_identity()
                user_name = principal_info["Arn"].split('/')[-1]
                principal_info_filtered = {
                    "UserId": principal_info["UserId"],
                    "Account": principal_info["Account"],
                    "Arn": principal_info["Arn"]
                }
            else:
                principal_info = self.get_caller_identity()
                role_arn = principal_info["Arn"]
                role_name = role_arn.split('/')[-2] if 'assumed-role' in role_arn else role_arn.split('/')[-1]
                principal_info_filtered = {
                    "RoleId": principal_info["UserId"],
                    "Account": principal_info["Account"],
                    "Arn": principal_info["Arn"],
                    "RoleName": role_name
                }
            print(yaml.dump(principal_info_filtered, default_flow_style=False))
        except Exception as e:
            print_red(f"  [!] Failed to retrieve {principal_type} information. Check AWS credentials. {str(e)}")
            return

        # Fetch attached managed policies
        print_cyan(f"\n[*] Attached {principal_type.title()} Policies:\n")
        try:
            if principal_type == 'user':
                attached_policies = self.list_attached_user_policies(user_name)
            else:
                attached_policies = self.list_attached_role_policies(role_name)
            print(yaml.dump(attached_policies))
        except Exception as e:
            print_red(f"  [!] Failed to retrieve attached policies: {str(e)}")
            attached_policies = []

        # Fetch inline policies
        print_cyan(f"\n[*] Inline {principal_type.title()} Policies:\n")
        try:
            if principal_type == 'user':
                inline_policies = self.list_user_policies(user_name)
            else:
                inline_policies = self.list_role_policies(role_name)
            print(yaml.dump(inline_policies))
        except Exception as e:
            print_red(f"  [!] Failed to retrieve inline policies: {str(e)}")
            inline_policies = []

        # Process all policies
        for policy in attached_policies:
            print_yellow(f"\n[*] Processing Attached Policy: {policy['PolicyArn']}\n")
            self.fetch_policy_details(policy_arn=policy['PolicyArn'])

        for policy_name in inline_policies:
            print_yellow(f"\n[*] Processing Inline Policy: {policy_name}\n")
            self.fetch_policy_details(
                is_inline=True,
                principal_type=principal_type,
                role_name=role_name,
                policy_name=policy_name
            )

    def fetch_policy_details(self, is_inline=False, policy_arn=None, principal_type=None, name=None, policy_name=None):
        try:
            if is_inline:
                if principal_type == 'role':
                    policy_document = self.get_role_policy(
                        role_name=name,
                        policy_name=policy_name
                    )
                else:  # user
                    policy_document = self.get_user_policy(
                        user_name=name,
                        policy_name=policy_name
                    )
            else:
                policy = self.get_policy(
                    policy_arn=policy_arn
                )
                policy_version = self.get_policy_version(
                    policy_arn=policy_arn,
                    version_id=policy['DefaultVersionId']
                )
                policy_document =  policy_version['Document']

            print(yaml.dump(policy_document)+'\n')

            for statement in policy_document.get('Statement', []):
                if statement.get('Effect').lower() == 'deny':
                    print("\n" + "-" * 100)
                    print_red(f"\n⛔ Skipping enumeration - Effect is DENY")
                    continue

                if statement.get('Condition'):
                    print("\n" + "-" * 100)
                    print_red(f"\n🔍 Conditions exist on this policy. Manual intervention needed.")
                    print(yaml.dump(statement))
                    continue

                actions = statement.get('Action', [])
                if isinstance(actions, str):
                    actions = [actions]

                resources = statement.get('Resource', [])
                if isinstance(resources, str):
                    resources = [resources]

                for action in actions:
                    for resource in resources:
                        is_resource_wildcard = resource == '*'
                        if resource != policy_arn:
                            self.enumerate_and_list_resources(action, resource, is_resource_wildcard)
                        self.check_interesting_permissions(action, resource)

        except Exception as e:
             print_red(f"  [!] Failed to retrieve policy details: {str(e)}")

    def list_specific_roles(self, role_patterns):
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