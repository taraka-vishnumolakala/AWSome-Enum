import boto3
import json
import yaml
from botocore.exceptions import ClientError
from tabulate import tabulate
from .utils import load_permissions, print_cyan, print_yellow, print_green, print_red

class AWSEnumerator:
    def __init__(self, profile=None):
        self.session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self.iam = self.session.client('iam')
        self.sts = self.session.client('sts')
        self.interesting_permissions = load_permissions()

    def check_interesting_permissions(self, actions):
        print_cyan("\n[*] Analyzing permissions for potential privilege escalation vectors:\n")
        for action in actions:
            if action in self.interesting_permissions:
                print_green(f"  [!] Interesting Permission Found: {action}")
                print_green(f"  ➡️  More info: {self.interesting_permissions[action]}")

    def get_caller_identity(self):
        return self.sts.get_caller_identity()

    def list_attached_user_policies(self, username):
        return self.iam.list_attached_user_policies(UserName=username)['AttachedPolicies']
    
    def list_attached_role_policies(self, rolename):
        return self.iam.list_attached_role_policies(RoleName=rolename)['AttachedPolicies']

    def list_user_policies(self, username):
        return self.iam.list_user_policies(UserName=username)['PolicyNames']
    
    def list_role_policies(self, rolename):
        return self.iam.list_role_policies(RoleName=rolename)['PolicyNames']

    def get_policy(self, policy_arn):
        return self.iam.get_policy(PolicyArn=policy_arn)['Policy']

    def get_policy_version(self, policy_arn, version_id):
        return self.iam.get_policy_version(PolicyArn=policy_arn, VersionId=version_id)['PolicyVersion']

    def get_user_policy(self, username, policy_name):
        return self.iam.get_user_policy(UserName=username, PolicyName=policy_name)['PolicyDocument']

    def list_roles(self):
        return self.iam.list_roles()['Roles']

    def extract_actions(self, policy_document):
        actions = []
        for statement in policy_document.get('Statement', []):
            action = statement.get('Action')
            if isinstance(action, str):
                actions.append(action)
            elif isinstance(action, list):
                actions.extend(action)
        return actions

    def check_and_list_identities(self, actions):
        if "iam:ListRoles" in actions or "iam:*" in actions:
            print_cyan("\n[*] Checking for IAM listing permissions:\n")
            print_yellow("\n[*] Found iam:ListRoles permission - Listing all roles:\n")
            roles = self.list_roles()
            role_data = [[role['RoleName'], role['Arn']] for role in roles]
            print(tabulate(role_data, headers=['Role Name', 'ARN'], tablefmt='plain'))

        if "iam:ListUsers" in actions or "iam:*" in actions:
            print_yellow("\n[*] Found iam:ListUsers permission - Listing all users:\n")
            users = self.iam.list_users()['Users']
            user_data = [[user['UserName'], user['Arn']] for user in users]
            print(tabulate(user_data, headers=['User Name', 'ARN'], tablefmt='plain'))

    def enumerate_permissions(self, principal_type):
        """
        Enumerate permissions for a given IAM principal (user or role)

        Args:
            principal_type (str): Type of principal ('user' or 'role')
        """
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
            print_red(f"  [!] Failed to retrieve {principal_type} information: {str(e)}")
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
            print_yellow(f"\n[*] Processing Managed Policy: {policy['PolicyArn']}\n")
            self.fetch_policy_details(policy_arn=policy['PolicyArn'])

        for policy_name in inline_policies:
            print_yellow(f"\n[*] Processing Inline Policy: {policy_name}\n")
            self.fetch_policy_details(
                is_inline=True,
                principal_type=principal_type,
                role_name=role_name,
                policy_name=policy_name
            )

    def fetch_policy_details(self, is_inline=False, policy_arn=None, principal_type=None, role_name=None, policy_name=None):
        """
        Fetch and display policy details for either inline or managed policies

        Args:
            is_inline (bool): Whether the policy is inline
            policy_arn (str): ARN of managed policy
            principal_type (str): Type of principal ('user' or 'role')
            policy_name (str): Name of the inline policy
        """
        try:
            if is_inline:
                if principal_type == 'role':
                    policy = self.iam_client.get_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name
                    )
                else:  # user
                    policy = self.iam_client.get_user_policy(
                        UserName=role_name,
                        PolicyName=policy_name
                    )
                print(yaml.dump(policy['PolicyDocument']))
            else:
                policy = self.iam_client.get_policy(
                    PolicyArn=policy_arn
                )['Policy']

                policy_version = self.iam_client.get_policy_version(
                    PolicyArn=policy_arn,
                    VersionId=policy['DefaultVersionId']
                )['PolicyVersion']

                print(yaml.dump(policy_version['Document']))
        except Exception as e:
            print_red(f"  [!] Failed to retrieve policy details: {str(e)}")
            print_cyan("\n" + "=" * 80)
            print_cyan("Enumerating User Permissions")
            print_cyan("=" * 80)

            print_cyan("\n[*] Fetching user identity information:\n")
            user_info = self.get_caller_identity()
            if not user_info:
                print("  [!] Failed to retrieve user identity. Check AWS credentials.")
                return

            user_info_filtered = {
                "UserId": user_info["UserId"],
                "Account": user_info["Account"],
                "Arn": user_info["Arn"]
            }

            print(yaml.dump(user_info_filtered, default_flow_style=False))

            username = user_info['Arn'].split('/')[-1]

            print_cyan("\n[*] Attached User Policies (Managed):\n")
            attached_policies = self.list_attached_user_policies(username)
            print(yaml.dump(attached_policies))

            print_cyan("\n[*] Inline User Policies:\n")
            inline_policies = self.list_user_policies(username)
            print(yaml.dump(inline_policies))

            for policy in attached_policies:
                print_yellow(f"\n[*] Processing Managed Policy: {policy['PolicyArn']}\n")
                self.fetch_policy_details(policy_arn=policy['PolicyArn'])

            for policy_name in inline_policies:
                print_yellow(f"\n[*] Processing Inline Policy: {policy_name}\n")
                self.fetch_policy_details(is_inline=True, username=username, policy_name=policy_name)

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