import boto3
from .utils import print_cyan, print_red
from .services import AVAILABLE_SERVICES, link_services

class AWSEnumerator:

    def __init__(self, profile=None):
        self.session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self.services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        for service_name in AVAILABLE_SERVICES:
            self.services[service_name] = AVAILABLE_SERVICES[service_name](self.session)
            
        # Link services for cross-service enumeration
        link_services(self.services)
    
    def get_service(self, service_name):
        if service_name not in self.services:
            self.services[service_name] = AVAILABLE_SERVICES[service_name](self.session)
            
        return self.services[service_name]
    
    def enumerate_all_services(self):
        for service_name in AVAILABLE_SERVICES:
            service = self.get_service(service_name)
            if service:
                print_cyan(f"\nEnumerating {service_name.upper()} Service...")
                service.enumerate()
        
    def enumerate_service(self, service_name):
        if service_name not in AVAILABLE_SERVICES:
            print_red(f"Service '{service_name}' is not implemented or available.")
            return None

        service = self.get_service(service_name)
        if not service:
            return {"error": f"Service '{service_name}' not available"}
            
        return service.enumerate()