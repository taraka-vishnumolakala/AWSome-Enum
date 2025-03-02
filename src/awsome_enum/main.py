import argparse
import sys
from .enumerator import AWSEnumerator
from .utils import print_compact_logo, print_red, print_cyan, print_yellow
from .services import AVAILABLE_SERVICES

# Define available subcommands for each service
SERVICE_SUBCOMMANDS = {
    'iam': {
        'find-roles': {
            'description': 'Finds all IAM roles with matching names',
            'usage': 'find-roles <pattern1> [<pattern2> ...]',
            'requires_args': True
        }
    },
    's3': {
        'get-all-buckets': {
            'description': 'List all S3 buckets in the account',
            'usage': 'get-all-buckets',
            'requires_args': False
        }
    }
    # Add other services and their subcommands as needed
}

def main():
    print_compact_logo()
    
    # Handle special case for help flags
    if len(sys.argv) == 1 or sys.argv[1].lower() == 'help':
        print_general_help()
        return
        
    # Create custom parser with add_help=False to handle -h/--help manually
    parser = argparse.ArgumentParser(
        description="AWSome-enum: AWS resource enumeration tool",
        usage="poetry run awsome-enum [-h] [-p PROFILE] [-e SERVICE] [subcommand] [args...]",
        add_help=False  # Disable built-in help to handle it manually
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show help message and exit")
    parser.add_argument("-p", "--profile", help="Specify an AWS CLI profile")
    parser.add_argument("-e", "--enumerate", dest="service", metavar="SERVICE",
                        help="Service to enumerate (e.g., iam, s3)")
    parser.add_argument("service_pos", nargs="?", help="Service to enumerate if using positional arguments")
    parser.add_argument("subcommand", nargs="?", help="Service-specific command to run")
    parser.add_argument("args", nargs="*", help="Additional arguments for the subcommand")

    # Special handling for problematic flag combinations
    if "-e" in sys.argv and len(sys.argv) > sys.argv.index("-e") + 1 and sys.argv[sys.argv.index("-e") + 1] == "-h":
        print_enumerate_help()
        return
    
    if "--enumerate" in sys.argv and len(sys.argv) > sys.argv.index("--enumerate") + 1 and sys.argv[sys.argv.index("--enumerate") + 1] == "-h":
        print_enumerate_help()
        return
        
    if "-p" in sys.argv and len(sys.argv) > sys.argv.index("-p") + 1 and sys.argv[sys.argv.index("-p") + 1] == "-h":
        print_general_help()
        return
        
    if "--profile" in sys.argv and len(sys.argv) > sys.argv.index("--profile") + 1 and sys.argv[sys.argv.index("--profile") + 1] == "-h":
        print_general_help()
        return

    # Parse arguments
    try:
        args, unknown = parser.parse_known_args()
        
        # Handle explicit help flag
        if args.help or "-h" in unknown or "--help" in unknown:
            if args.service:
                service_name = args.service.lower()
                if service_name in AVAILABLE_SERVICES:
                    # Show service-specific help with hardcoded subcommands
                    print_service_subcommands(service_name)
                else:
                    print_red(f"Unknown service: {service_name}")
                    print_enumerate_help()
            else:
                print_general_help()
            return
    except Exception:
        # Fall back to general help on parsing errors
        print_general_help()
        return
    
    # Determine which service to use (from -e flag or positional arguments)
    service_name = None
    subcommand = args.subcommand
    
    if args.service:
        # Using -e/--enumerate flag
        service_name = args.service
        # When using -e flag, subcommand might be in the service_pos position
        if not subcommand and args.service_pos:
            subcommand = args.service_pos
    elif args.command == "enumerate" and args.service_pos:
        # Using positional arguments (enumerate service)
        service_name = args.service_pos
    elif args.command and args.command.lower() in AVAILABLE_SERVICES:
        # User might have typed "AWSome-enum iam" directly
        service_name = args.command
        subcommand = args.service_pos  # Shift arguments
    
    # Handle help requests
    if service_name and service_name.lower() == "help":
        print_enumerate_help()
        return
    elif subcommand and subcommand.lower() == "help":
        if service_name and service_name.lower() in AVAILABLE_SERVICES:
            print_service_subcommands(service_name.lower())
        else:
            print_enumerate_help()
        return
    
    # Handle no service specified
    if not service_name:
        if args.command == "enumerate":
            print_enumerate_help()
        else:
            print_general_help()
        return
    
    # Initialize the AWS Enumerator and get service
    enumerator = AWSEnumerator(profile=args.profile)
    service = enumerator.get_service(service_name.lower())
    
    if not service:
        print_red(f"Service '{service_name}' is not implemented or available.")
        print_enumerate_help()
        return
    
    # Execute commands
    if not subcommand:
        service.enumerate()
    else:
        execute_service_command(service, service_name.lower(), subcommand, args.args)

def print_general_help():
    """Print general help information."""
    print_cyan("\nUsage: poetry run awsome-enum [-h] [-p PROFILE] [-e SERVICE] [subcommand] [args...]")
    print("\nOptions:")
    print("  -h, --help             Show this help message and exit")
    print("  -p, --profile PROFILE  Specify an AWS CLI profile")
    print("  -e, --enumerate SERVICE  Service to enumerate (e.g., iam, s3)")
    print("\nAlternate Usage:")
    print("poetry run awsome-enum --enumerate <service> [<subcommand>] [<args>...]")
    print("\nFor more information on enumeration, run: poetry run awsome-enum -e help")

def print_enumerate_help():
    """Print help for the enumerate command."""
    print_cyan("\nUsage: poetry run awsome-enum [-e SERVICE] or awsome-enum --enumerate <service>")
    print("\nEnumerate AWS services and resources")
    print("\nAvailable services:")
    
    for service_name in sorted(AVAILABLE_SERVICES.keys()):
        print(f"  {service_name}")
    
    print("\nExamples:")
    print("  poetry run awsome-enum -e iam")
    print("  poetry run awsome-enum --enumerate iam")
    print("\nFor service-specific commands, use: poetry run awsome-enum -e <service> help")

def print_service_subcommands(service_name):
    """Print available subcommands for a service using predefined list."""
    print_cyan(f"\nAvailable subcommands for {service_name.upper()} service:")
    
    # Get subcommands from the hardcoded dictionary
    subcommands = SERVICE_SUBCOMMANDS.get(service_name, {})
    
    if subcommands:
        print("\nCommand                     Description")
        print("-------------------------  ------------------------------------------------")
        
        for cmd, info in sorted(subcommands.items()):
            print(f"  {cmd:<25} {info['description']}")
        
        print("\nUsage examples:")
        for cmd, info in sorted(subcommands.items()):
            print(f"  poetry run awsome-enum -e {service_name} {info['usage']}")
    else:
        print_yellow(f"  No additional subcommands available for {service_name}")
        print(f"  Use 'poetry run awsome-enum -e {service_name}' for basic enumeration")

def execute_service_command(service, service_name, subcommand, arguments):
    """Execute a subcommand for a service."""
    # Check if the subcommand is valid for this service
    if service_name not in SERVICE_SUBCOMMANDS or subcommand not in SERVICE_SUBCOMMANDS[service_name]:
        print_red(f"Unknown subcommand '{subcommand}' for service '{service_name}'")
        print_service_subcommands(service_name)
        return
    
    # Convert kebab-case to snake_case (e.g., list-roles -> list_roles)
    method_name = subcommand.replace("-", "_")
    
    # Get the method from the service
    method = getattr(service, method_name)
    
    # Get command information
    cmd_info = SERVICE_SUBCOMMANDS[service_name][subcommand]
    
    # Check if arguments are required
    requires_args = cmd_info.get('requires_args', False)
        
    # Validate arguments if needed
    if requires_args and not arguments:
        print_red(f"This subcommand requires additional arguments")
        print_yellow(f"Usage: poetry run awsome-enum -e {service_name} {cmd_info.get('usage', "")}")
        return
        
    # Call the method with arguments if provided
    try:
        if arguments:
            method(arguments)
        else:
            method()
    except Exception as e:
        print_red(f"Error executing {subcommand}: {str(e)}")

if __name__ == "__main__":
    main()