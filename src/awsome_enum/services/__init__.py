from .iam import IAMService
from .s3 import S3Service
from .secretsmanager import SecretsManagerService
from .kms import KMSService
from .ec2 import EC2Service
# Import other services as they are implemented

# This dictionary will be used to load and instantiate service classes
AVAILABLE_SERVICES = {
    'iam': IAMService,
    's3': S3Service,
    'secretsmanager': SecretsManagerService,
    'kms': KMSService,
    'ec2': EC2Service,
    # Add other services here as they are implemented
}