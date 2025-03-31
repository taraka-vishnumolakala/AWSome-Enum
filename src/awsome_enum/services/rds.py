from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta

class RDSService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'rds', debug)
        self.supported_actions = [
            "rds:*",
            "rds:DescribeDBInstances",
            "rds:DescribeDBSnapshots"
        ]

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating RDS Resources")
        print_cyan("*" * 80)

        try:
            instances = self.list_db_instances()
            if not instances:
                print_yellow("No RDS instances found.")
                return

            for instance in instances:
                self._display_instance_info(instance)

            self._handle_describe_snapshots("rds:DescribeDBSnapshots", "*")

        except Exception as e:
            print_red(f"Error enumerating RDS resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        if "rds:DescribeDBInstances" == action or "rds:*" in action:
            self._handle_describe_instances(action, resource)
        elif "rds:DescribeDBSnapshots" == action or "rds:*" in action:
            self._handle_describe_snapshots(action, resource)

    def _handle_describe_instances(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing RDS instances")
        instances = self.list_db_instances()
        if not instances:
            print_yellow("No RDS instances found.")
            return
        
        for instance in instances:
            self._display_instance_info(instance)

    def _display_instance_info(self, instance):
        print_yellow(f"\n[*] DB Instance: {instance.get('DBInstanceIdentifier')}")
        
        instance_data = [
            ['Engine', instance.get('Engine')],
            ['Engine Version', instance.get('EngineVersion')],
            ['Status', instance.get('DBInstanceStatus')],
            ['Class', instance.get('DBInstanceClass')],
            ['Storage', f"{instance.get('AllocatedStorage')} GB"],
            ['Endpoint', f"{instance.get('Endpoint', {}).get('Address', 'N/A')}:{instance.get('Endpoint', {}).get('Port', 'N/A')}"],
            ['Master Username', instance.get('MasterUsername')],
            ['DB Name', instance.get('DBName')],
            ['VPC ID', instance.get('DBSubnetGroup', {}).get('VpcId')],
        ]
        print(tabulate(instance_data, tablefmt='plain'))

        if vpc_groups := instance.get('VpcSecurityGroups', []):
            print_yellow("\nVPC Security Groups:")
            for group in vpc_groups:
                print(f"ID: {group.get('VpcSecurityGroupId')} (Status: {group.get('Status')})")

    def _handle_describe_snapshots(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Checking for public snapshots")
        
        try:
            sts_client = self.session.client('sts')
            account_id = sts_client.get_caller_identity().get('Account')
            print_yellow(f"\nChecking public snapshots for account: {account_id}")
    
            public_snapshots = self.list_public_snapshots(account_id)
            if public_snapshots:
                print_yellow("\nPublic DB Snapshots:")
                self._display_snapshots(public_snapshots)
                print_red("\n[!] Warning: Public snapshots found! These might expose sensitive data.")
            else:
                print_yellow("No public DB snapshots found.")
    
        except Exception as e:
            if self.debug:
                print_red(f"Error listing snapshots: {str(e)}")

    def _display_snapshots(self, snapshots):
        table_data = []
        for snapshot in snapshots:
            table_data.append([
                snapshot.get('DBSnapshotIdentifier'),
                snapshot.get('DBInstanceIdentifier'),
                snapshot.get('Engine'),
                snapshot.get('EngineVersion'),
                f"{snapshot.get('AllocatedStorage')} GB",
                snapshot.get('MasterUsername'),
                'No' if snapshot.get('Encrypted', False) else 'Yes',
                snapshot.get('SnapshotCreateTime').strftime('%Y-%m-%d %H:%M:%S') if snapshot.get('SnapshotCreateTime') else 'N/A'
            ])
    
    def list_public_snapshots(self, account_id):
        try:
            response = self.client.describe_db_snapshots(
                IncludePublic=True,
                SnapshotType='public'
            )
    
            snapshots = response.get('DBSnapshots', [])
            account_pattern = f"{account_id}:"
            filtered_snapshots = [
                snapshot for snapshot in snapshots 
                if account_pattern in snapshot.get('DBSnapshotIdentifier', '')
            ]
    
            return filtered_snapshots
    
        except Exception as e:
            if self.debug:
                print_red(f"Error listing public DB snapshots: {str(e)}")
            return []

    def list_db_instances(self):
        response = self.client.describe_db_instances()
        return response.get('DBInstances', [])
