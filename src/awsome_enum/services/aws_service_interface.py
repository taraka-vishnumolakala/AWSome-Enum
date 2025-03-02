from abc import ABC, abstractmethod
import boto3

class AWSServiceInterface(ABC):
    """Base interface for all AWS services to implement."""
    
    def __init__(self, session=None, service_name=None):
        self.session = session or boto3.Session()
        self.service_name = service_name
        if not self.service_name:
            raise ValueError("service_name must be provided")
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the boto3 client for this aws service."""
        return self.session.client(self.service_name)
    
    @abstractmethod
    def enumerate(self):
        """
        Enumerate resources and permissions for this service.
        This is the main entry point for service enumeration.
        """
        pass
    
    def handle_permission_action(self, action, resource, is_resource_wildcard=False):
        """
        Handle a specific permission action that's been discovered.
        This allows for targeted enumeration based on permissions found in policy documents.
        
        Args:
            action (str): The permission action (e.g., 's3:ListBuckets')
            resource (str): The resource ARN or wildcard
            is_resource_wildcard (bool): Whether the resource is a wildcard
            
        Returns:
            None
        """
        # Default implementation does nothing
        # Each service should override this to provide targeted, permission-specific enumeration
        print(f"No specific handler for action {action} on resource {resource}")
        return None