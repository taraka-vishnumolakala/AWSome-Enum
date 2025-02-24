import argparse
from .enumerator import AWSEnumerator

def main():
    parser = argparse.ArgumentParser(
        description="An AWS security tool that systematically analyzes permissions and policies, uncovering potential privilege escalation paths.",
        usage="%(prog)s [-h] [--profile PROFILE] <command> [<args>]"
    )
    parser.add_argument("--profile", help="Specify an AWS CLI profile")
    
    subparsers = parser.add_subparsers(dest="command", title="commands", metavar="")
    
    # Enumerate user permissions command
    enumerate_user_parser = subparsers.add_parser("enumerate-user-permissions", help="Enumerate and analyze permissions for the current user")
    enumerate_role_parser = subparsers.add_parser("enumerate-role-permissions", help="Enumerate and analyze permissions for the current role")


    # List roles command
    list_roles_parser = subparsers.add_parser("list-roles", help="Search for specific IAM roles")
    list_roles_parser.add_argument("patterns", nargs="+", help="One or more patterns to match role names")
    
    args = parser.parse_args()

    if args.command == "enumerate-user-permissions":
        enumerator = AWSEnumerator(profile=args.profile)
        enumerator.enumerate_permissions(principal_type='user')
    elif args.command == "enumerate-role-permissions":
        enumerator = AWSEnumerator(profile=args.profile)
        enumerator.enumerate_permissions(principal_type='role')
    elif args.command == "list-roles":
        enumerator = AWSEnumerator(profile=args.profile)
        enumerator.list_specific_roles(args.patterns)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()