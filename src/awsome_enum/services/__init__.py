from .iam import IAMService
from .s3 import S3Service
from .secretsmanager import SecretsManagerService
from .kms import KMSService
from .ec2 import EC2Service
from .lightsail import LightsailService
from .lambda_service import LambdaService
from .efs import EFSService
from .rds import RDSService
from .ecr import ECRService
from .ecs import ECSService
from .elasticbeanstalk import ElasticBeanstalkService
from .codebuild import CodeBuildService
from .sqs import SQSService
from .sns import SNSService
from .stepfunctions import StepFunctionsService
from .eventbridgescheduler import EventBridgeSchedulerService
# Import other services as they are implemented

# This dictionary will be used to load and instantiate service classes
AVAILABLE_SERVICES = {
    'iam': IAMService,
    's3': S3Service,
    'secretsmanager': SecretsManagerService,
    'kms': KMSService,
    'ec2': EC2Service,
    'lightsail': LightsailService,
    'lambda': LambdaService,
    'efs': EFSService,
    'rds': RDSService,
    'ecr': ECRService,
    'ecs': ECSService,
    'elasticbeanstalk': ElasticBeanstalkService,
    'codebuild': CodeBuildService,
    'sqs': SQSService,
    'sns': SNSService,
    'states': StepFunctionsService,
    'scheduler': EventBridgeSchedulerService,
    # Add other services here as they are implemented
}