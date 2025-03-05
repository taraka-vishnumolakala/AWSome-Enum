from abc import ABC, abstractmethod
import boto3
import yaml
from ..utils import load_permissions, print_green, print_red

class AWSServiceInterface(ABC):
    """Base interface for all AWS services to implement."""
    
    def __init__(self, session=None, service_name=None, debug=False):
        self.session = session
        self.service_name = service_name
        self.debug = debug
        self.interesting_permissions = load_permissions()
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the boto3 client for this aws service."""
        return self.session.client(self.service_name)
    
    def check_interesting_permissions(self, action, resource):
        """
        Check if a permission action is interesting and print a message if it is.
    
        Args:
            action (str): The AWS IAM action to check (e.g., 'iam:PassRole')
            resource (str): The AWS resource ARN the action applies to
    
        Prints privilege escalation info if the action is interesting.
        """
        if action in self.interesting_permissions:
            print()
            print_green(f"[!] '{action}' is an Interesting Permission for possible privilege escalation.")
            print_green(f"➡️  More info: {self.interesting_permissions[action]}")
            print_green(f"🎯 Resource: {resource}")

    def parse_policy_document(self, policy_document):
        """
        Parse a policy document and extract the actions and resources.
        
        Args:
            policy_document (dict): The policy document to parse
        
        Returns:
            dict: A dictionary mapping resources to actions
        """
        resource_actions = {}
    
        for statement in policy_document.get('Statement', []):
            if statement.get('Effect', '').lower() == 'deny':
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
    
            for resource in resources:
                if resource not in resource_actions:
                    resource_actions[resource] = []
                resource_actions[resource].extend(actions)
    
        # Remove duplicates from action lists
        for resource in resource_actions:
            resource_actions[resource] = list(set(resource_actions[resource]))
    
        return resource_actions
    
    def handle_unimplemented_action(self, action, resource):
        print_red(f"\n❌ Action '{action}' is set on resource '{resource}'")
        print_red("   Manual investigation recommended as this permission is not currently supported.")
    
    @abstractmethod
    def enumerate(self):
        """
        Enumerate resources and permissions for this service.
        This is the main entry point for service enumeration.
        """
        pass
    
    @abstractmethod
    def handle_permission_action(self, action, resource):
        """
        Handle a specific permission action that's been discovered.
        This allows for targeted enumeration based on permissions found in policy documents.
        
        Args:
            action (str): The permission action (e.g., 's3:ListBuckets')
            resource (str): The resource ARN or wildcard
            
        Returns:
            None
        """
        pass