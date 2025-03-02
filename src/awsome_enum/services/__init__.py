from .iam import IAMService
from .s3 import S3Service
# Import other services as they are implemented

# This dictionary will be used to load and instantiate service classes
AVAILABLE_SERVICES = {
    'iam': IAMService,
    's3': S3Service,
    # Add other services here as they are implemented
    # 'secretsmanager': SecretsManagerService,
    # 'kms': KMSService,
}

# Make sure IAM service knows about other services for cross-service enumeration
def link_services(services_dict):
    """
    Link services together for cross-service enumeration.
    Currently, only IAM service needs to know about other services.
    """
    for service_name, service_instance in services_dict.items():
        if service_name == 'iam' and hasattr(service_instance, 'set_available_services'):
            service_instance.set_available_services(AVAILABLE_SERVICES)