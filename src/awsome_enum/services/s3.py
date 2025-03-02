import yaml
from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from ..utils import print_cyan, print_yellow, print_red, print_green

class S3Service(AWSServiceInterface):
    """Implementation of AWS S3 service enumeration and exploitation."""
    
    def __init__(self, session=None):
        super().__init__(session, 's3')
    
    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating S3 Resources")
        print_cyan("*" * 80)
        
        try:
            buckets = self.list_buckets()
            
            if not buckets:
                print_yellow("No S3 buckets found.")
                return
                
            bucket_data = [[bucket['Name'], bucket['CreationDate']] for bucket in buckets]
            print_cyan("\n[*] S3 Buckets Found:\n")
            print(tabulate(bucket_data, headers=['Bucket Name', 'Creation Date'], tablefmt='plain'))
            
            # For each bucket, get additional details
            for bucket in buckets:
                self._enumerate_bucket_details(bucket['Name'])
                
        except Exception as e:
            print_red(f"Error enumerating S3 resources: {str(e)}")
            
    def handle_permission_action(self, action, resource, is_resource_wildcard=False):
        """Handle specific S3 permissions discovered in IAM policies."""
        print_cyan(f"\n[*] Handling S3 permission: {action} on resource: {resource}")
        
        # Check for specific S3 actions
        if "s3:ListAllMyBuckets" in action or "s3:*" in action:
            print_yellow("\n[*] Found s3:ListAllMyBuckets permission - Listing all buckets:\n")
            self._list_and_display_buckets()
            
        # Check if action relates to a specific bucket
        if resource != '*' and resource.startswith('arn:aws:s3:::'):
            bucket_name = resource.split(':::')[1].split('/')[0]
            print_yellow(f"\n[*] Found permissions for bucket: {bucket_name}")
            
            # Check bucket policy if we have permission
            if "s3:GetBucketPolicy" in action or "s3:*" in action:
                self._check_bucket_policy(bucket_name)
                
            # Check bucket objects if we have permission
            if "s3:ListBucket" in action or "s3:*" in action:
                self._list_bucket_objects(bucket_name)
    
    def _list_and_display_buckets(self):
        """List and display S3 buckets."""
        try:
            buckets = self.list_buckets()
            if not buckets:
                print_yellow("No S3 buckets found.")
                return
                
            bucket_data = [[bucket['Name'], bucket['CreationDate']] for bucket in buckets]
            print(tabulate(bucket_data, headers=['Bucket Name', 'Creation Date'], tablefmt='plain'))
        except Exception as e:
            print_red(f"Error listing buckets: {str(e)}")
    
    def _enumerate_bucket_details(self, bucket_name):
        """Get details for a specific bucket."""
        print_cyan(f"\n[*] Enumerating details for bucket: {bucket_name}")
        
        try:
            # Check bucket policy
            self._check_bucket_policy(bucket_name)
            
            # List bucket objects (first 20)
            self._list_bucket_objects(bucket_name, max_keys=20)
            
        except Exception as e:
            print_red(f"Error enumerating bucket {bucket_name}: {str(e)}")
    
    def _check_bucket_policy(self, bucket_name):
        """Check bucket policy if it exists."""
        try:
            policy = self.client.get_bucket_policy(Bucket=bucket_name)
            print_yellow(f"\n[*] Bucket Policy for {bucket_name}:")
            print(yaml.dump(yaml.safe_load(policy['Policy']), default_flow_style=False))
        except self.client.exceptions.NoSuchBucketPolicy:
            print_yellow(f"No bucket policy found for {bucket_name}")
        except Exception as e:
            print_red(f"Error getting bucket policy: {str(e)}")
    
    def _list_bucket_objects(self, bucket_name, max_keys=20):
        """List objects in a bucket."""
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