import json
import yaml
from colorama import Fore, Style, init

def load_permissions():
    try:
        with open("interesting_permissions.json", "r") as f:
            permissions = json.load(f)
        # print(f"Loaded {len(permissions)} interesting permissions.")
        return permissions
    except FileNotFoundError:
        print("Warning: interesting_permissions.json not found in the current directory. Interesting permissions will not be checked.")
    except json.JSONDecodeError:
        print("Error: interesting_permissions.json is not valid JSON. Please check the file format.")
    except Exception as e:
        print(f"An error occurred while loading interesting_permissions.json: {str(e)}")
    return {}

def print_compact_logo():
    init()
    logo = """
     █████╗ ██╗    ██╗███████╗ ██████╗ ███╗   ███╗███████╗      ███████╗███╗   ██╗██╗   ██╗███╗   ███╗
    ██╔══██╗██║    ██║██╔════╝██╔═══██╗████╗ ████║██╔════╝      ██╔════╝████╗  ██║██║   ██║████╗ ████║
    ███████║██║ █╗ ██║███████╗██║   ██║██╔████╔██║█████╗        ███████╗██╔██╗ ██║██║   ██║██╔████╔██║
    ██╔══██║██║███╗██║╚════██║██║   ██║██║╚██╔╝██║██╔══╝        ██╔════╝██║╚██╗██║██║   ██║██║╚██╔╝██║
    ██║  ██║╚███╔███╔╝███████║╚██████╔╝██║ ╚═╝ ██║███████╗      ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
    ╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝      ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝
    """
    print(f"{Fore.YELLOW}{logo}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}                         AWSome-enum v1.0.0{Style.RESET_ALL}")
    print("\nAn AWS security enumeration tool that recursively analyzes permissions, policies, and suggests potential privilege escalation paths.")
    print("-" * 80)


def print_interesting_permissions(self, action, resource):
    print("\n")
    print_green(f"[!] '{action}' is an Interesting Permission for possible privilege escalation.")
    print_green(f"➡️  More info: {self.interesting_permissions[action]}")
    print_green(f"🎯 Resource: {resource}")  

def print_green(message):
    print(f"\033[92m{message}\033[0m")

def print_yellow(message):
    print(f"\033[93m{message}\033[0m")

def print_cyan(message):
    print(f"\033[96m{message}\033[0m")

def print_red(message):
    print(f"\033[91m{message}\033[0m")

def print_magenta(message):
    print(f"\033[95m{message}\033[0m")