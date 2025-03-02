# Define available subcommands for each service
SERVICE_SUBCOMMANDS = {
    'iam': {
        'find-roles': {
            'description': 'Finds all IAM roles with matching names',
            'usage': 'find-roles <pattern1> [<pattern2> ...]',
            'requires_args': True
        }
    },
    's3': {
        'get-all-buckets': {
            'description': 'List all S3 buckets in the account',
            'usage': 'get-all-buckets',
            'requires_args': False
        }
    }
    # Add other services and their subcommands as needed
}