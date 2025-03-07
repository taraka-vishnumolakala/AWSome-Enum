import yaml
from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta

class S3Service(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 's3', debug)
        self.supported_actions = ["s3:ListAllMyBuckets", "s3:GetBucketPolicy", "s3:ListBucket", "s3:*"]
    
    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating S3 Resources")
        print_cyan("*" * 80)
        
        try:
            buckets = self._list_and_display_buckets()
            
            for bucket in buckets:
                self._enumerate_bucket_details(bucket['Name'])
                
        except Exception as e:
            print_red(f"Error enumerating S3 resources: {str(e)}")
            
    def handle_permission_action(self, action, resource):
        if "s3:ListAllMyBuckets" in action or "s3:*" in action:
            print_yellow("\n[*] Found s3:ListAllMyBuckets permission - Listing all buckets:\n")
            buckets = self._list_and_display_buckets()
            if buckets:
                print_magenta("\n💡 Tip: Use 'awsome-enum --profile [profile] -e s3' to iteratively enumerate all buckets")
            
        elif resource != '*' and resource.startswith('arn:aws:s3:::'):
            bucket_name = resource.split(':::')[1].split('/')[0]
            print_yellow(f"\n[*] Found permissions for bucket: {bucket_name}")
            
            if "s3:GetBucketPolicy" in action or "s3:*" in action:
                self._check_bucket_policy(bucket_name)
                
            if "s3:ListBucket" in action or "s3:*" in action:
                self._list_bucket_objects(bucket_name)

    def _enumerate_bucket_details(self, bucket_name):
        print_cyan(f"\n[*] Enumerating details for bucket: {bucket_name}")
        
        try:
            self._check_bucket_policy(bucket_name)            
            self._list_bucket_objects(bucket_name, max_keys=20)
            
        except Exception as e:
            print_red(f"Error enumerating bucket {bucket_name}: {str(e)}")
    
    def _list_and_display_buckets(self):
        try:
            buckets = self.list_buckets()
            if not buckets:
                print_yellow("No S3 buckets found.")
                return
                
            bucket_data = [[bucket['Name'], bucket['CreationDate']] for bucket in buckets]
            print_cyan("\n[*] S3 Buckets Found:\n")
            print(tabulate(bucket_data, headers=['Bucket Name', 'Creation Date'], tablefmt='plain'))
            return buckets
        except Exception as e:
            print_red(f"Error listing buckets: {str(e)}")
    
    def _check_bucket_policy(self, bucket_name):
        try:
            policy = self.client.get_bucket_policy(Bucket=bucket_name)
            print_yellow(f"\n[*] Bucket Policy for {bucket_name}:")
            print(yaml.dump(yaml.safe_load(policy['Policy']), default_flow_style=False))
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucketPolicy':
                print_red(f"No bucket policy found for {bucket_name}")
            else:
                print_red(f"Error getting bucket policy: {str(e)}")
        except Exception as e:
            print_red(f"Error getting bucket policy: {str(e)}")
    
    def _list_bucket_objects(self, bucket_name, max_keys=20):
        try:
            objects = self.client.list_objects_v2(Bucket=bucket_name, MaxKeys=max_keys)
            
            if 'Contents' not in objects or not objects['Contents']:
                print_yellow(f"No objects found in bucket {bucket_name}")
                return
                
            print_yellow(f"\n[*] Objects in bucket {bucket_name} (first {max_keys}):")
            object_data = [[obj['Key'], obj['Size'], obj['LastModified']] for obj in objects['Contents']]
            print(tabulate(object_data, headers=['Key', 'Size', 'Last Modified'], tablefmt='plain'))
            
            if objects.get('IsTruncated'):
                print_green(f"More than {max_keys} objects exist in this bucket.")
        except Exception as e:
            print_red(f"Error listing bucket objects: {str(e)}")
    
    # Wrapper methods for S3 API calls
    def list_buckets(self):
        response = self.client.list_buckets()
        return response.get('Buckets', [])