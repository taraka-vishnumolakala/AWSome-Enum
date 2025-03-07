# Define available subcommands for each service
SERVICE_SUBCOMMANDS = {
    'iam': {
        'find-role': {
            'description': 'Finds an IAM role with matching name',
            'usage': 'find-role [role-name]',
            'requires_args': True
        }
    },
    's3': {
        'get-all-buckets': {
            'description': 'List all S3 buckets in the account',
            'usage': 'get-all-buckets',
            'requires_args': False
        }
    },
    'ec2': {
        'describe-instance-attribute': {
            'description': 'Describes the specified attribute of the specified instance',
            'usage': 'describe-instance-attribute <instance-id> <attribute>',
            'requires_args': True
        }
    }
    # Add other services and their subcommands as needed
}