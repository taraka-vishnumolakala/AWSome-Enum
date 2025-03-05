import argparse
import sys
from .enumerator import AWSEnumerator
from .utils import print_compact_logo, print_red, print_cyan, print_yellow
from .services import AVAILABLE_SERVICES
from .service_subcommands import SERVICE_SUBCOMMANDS

def main():
    print_compact_logo()
    
    parser = argparse.ArgumentParser(
        description="AWSome-enum: AWS resource enumeration tool",
        add_help=False
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show help message and exit")
    parser.add_argument("-p", "--profile", help="Specify an AWS CLI profile")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument("-e", "--enumerate", dest="service", metavar="SERVICE", 
                        nargs="?", const="", 
                        help="Service to enumerate (e.g., iam, s3). Use without a value to enumerate all services.")
    
    try:
        args, remaining = parser.parse_known_args()                
        
        if args.help:
            if args.service == "":
                print_enumerate_help()
                return
            elif args.service and args.service.lower() in AVAILABLE_SERVICES:
                print_service_subcommands(args.service.lower())
                return
            elif args.service:
                print_enumerate_help()
                return
            else:
                print_general_help()
                return
        
        if args.service is None:
            print_general_help()
            return

        if args.service == "":
            enumerator = AWSEnumerator(profile=args.profile, debug=args.debug)
            enumerator.enumerate_all_services()
            return
        
        service_name = args.service.lower()
        if service_name not in AVAILABLE_SERVICES:
            print_red(f"Service '{service_name}' is not implemented or available.")
            print_enumerate_help()
            return
        
        enumerator = AWSEnumerator(profile=args.profile, debug=args.debug)
        service = enumerator.get_service_instance(service_name)
        
        if not remaining:
            service.enumerate()
            return
        
        subcommand = remaining[0]
        subcommand_args = remaining[1:] if len(remaining) > 1 else []
        
        if subcommand.lower() in ['-h', '--help']:
            print_service_subcommands(service_name)
            return
        
        execute_service_command(service, service_name, subcommand, subcommand_args)
    
    except Exception as e:
        print_red(f"Error: {str(e)}")
        print_general_help()
        return

def print_general_help():
    print_cyan("\nUsage: poetry run awsome-enum [-h] [-p PROFILE] [-e [SERVICE]] [subcommand] [args...]")
    print("\nOptions:")
    print("  -h, --help                 # Show help message and exit")
    print("  -p, --profile [PROFILE]    # Specify an AWS CLI profile")
    print("  -e, --enumerate [SERVICE]  # Service to enumerate (e.g., iam, s3, lambda, etc.)")
    print("                               Use without a value to enumerate all services")
    
    print("\nUsage Examples:")
    print("  poetry run awsome-enum -h                                    # Show this help message")
    print("  poetry run awsome-enum -p [PROFILE] -e [SERVICE] -h          # Show available service-specific commands")
    
def print_enumerate_help():
    print_cyan("\nUsage: poetry run awsome-enum -e [SERVICE] [subcommand] [args...]")
    print("\nEnumerate AWS services and resources")
    print("\nAvailable services:")
    
    for service_name in sorted(AVAILABLE_SERVICES.keys()):
        print(f"  {service_name}")
    
    print("\nEnumeration Examples:")
    print("  poetry run awsome-enum --p [PROFILE] -e                       # Enumerates all services with default profile")
    print("  poetry run awsome-enum -p [PROFILE] -e [SERVICE] -h           # Show available service-specific commands")
    print("  poetry run awsome-enum -p [PROFILE] -e [SERVICE] [subcommand] [args...]  # Execute a specific subcommand")

def print_service_subcommands(service_name):
    print_cyan(f"\nAvailable subcommands for {service_name.upper()} service:")
    
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
    if service_name not in SERVICE_SUBCOMMANDS or subcommand not in SERVICE_SUBCOMMANDS[service_name]:
        print_red(f"Unknown subcommand '{subcommand}' for service '{service_name}'")
        print_service_subcommands(service_name)
        return
    
    method_name = subcommand.replace("-", "_")
    
    method = getattr(service, method_name, None)
    
    if method is None:
        print_red(f"Method '{method_name}' not found in service '{service_name}'")
        return
    
    cmd_info = SERVICE_SUBCOMMANDS[service_name][subcommand]
    
    requires_args = cmd_info.get('requires_args', False)
    
    if requires_args and not arguments:
        print_red(f"This subcommand requires additional arguments")
        print_yellow(f"Usage: poetry run awsome-enum -e {service_name} {cmd_info.get('usage', '')}")
        return
    
    try:
        if arguments:
            method(arguments)
        else:
            method()
    except Exception as e:
        print_red(f"Error executing {subcommand}: {str(e)}")

if __name__ == "__main__":
    main()