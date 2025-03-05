import boto3
from .utils import print_cyan, print_red
from .services import AVAILABLE_SERVICES

class AWSEnumerator:

    def __init__(self, profile=None, debug=False):
        self.session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self.debug = debug
        self.services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        for service_name in AVAILABLE_SERVICES:
            self.services[service_name] = AVAILABLE_SERVICES[service_name](
                session=self.session,
                debug=self.debug    
            )
            
        # Pass all service instances to the IAM service
        self.services['iam'].set_available_services(self.services)
    
    def get_service_instance(self, service_name):
        if service_name not in self.services:
            self.services[service_name] = AVAILABLE_SERVICES[service_name](
                session=self.session,
                debug=self.debug    
            )
            
        return self.services[service_name]
    
    def enumerate_all_services(self):
        service_name='iam'
        service = self.get_service_instance(service_name)
        if not service:
            return {"error": f"Service '{service_name}' not available"}
            
        return service.enumerate()