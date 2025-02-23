import boto3
import json
import yaml
from botocore.exceptions import ClientError
from tabulate import tabulate
from .utils import load_permissions, print_cyan, print_yellow, print_green

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

    def list_user_policies(self, username):
        return self.iam.list_user_policies(UserName=username)['PolicyNames']

    def get_policy(self, policy_arn):
        return self.iam.get_policy(PolicyArn=policy_arn)['Policy']

    def get_policy_version(self, policy_arn, version_id):
        return self.iam.get_policy_version(PolicyArn=policy_arn, VersionId=version_id)['PolicyVersion']

    def get_user_policy(self, username, policy_name):
        return self.iam.get_user_policy(UserName=username, PolicyName=policy_name)['PolicyDocument']

    def list_roles(self):
        return self.iam.list_roles()['Roles']

    def fetch_policy_details(self, policy_arn=None, is_inline=False, username=None, policy_name=None):
        if is_inline:
            policy_document = self.get_user_policy(username, policy_name)
            print_cyan(f"\n[*] Inline Policy Details: {policy_name}\n")
        else:
            policy = self.get_policy(policy_arn)
            policy_version = self.get_policy_version(policy_arn, policy['DefaultVersionId'])
            policy_document = policy_version['Document']
            print_cyan(f"\n[*] Policy Version Details: {policy_arn}\n")

        print(yaml.dump(policy_document))

        actions = self.extract_actions(policy_document)
        self.check_and_list_identities(actions)
        self.check_interesting_permissions(actions)

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

    def enumerate_user_permissions(self):
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
                    print_green(json.dumps(role, indent=2))
            else:
                print_yellow(f"  No roles found matching pattern: {pattern}")

        if not found_roles:
            print_yellow("\nNo matching roles found for any of the provided patterns.")