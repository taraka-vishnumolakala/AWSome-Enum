import yaml
from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta

class EFSService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'efs', debug)
        self.ec2_client = session.client('ec2') if session else None
        self.supported_actions = [
            "efs:Describe*",
            "efs:DescribeFileSystems",
            "efs:DescribeFileSystemPolicy",
            "efs:DescribeMountTargets",
            "efs:DescribeMountTargetSecurityGroups",
            "efs:DescribeAccessPoints",
            "efs:DescribeReplicationConfigurations"
        ]

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating EFS Resources")
        print_cyan("*" * 80)
        
        try:
            filesystems = self.describe_file_systems()
            if not filesystems:
                print_yellow("No EFS filesystems found.")
                return

            for fs in filesystems:
                fs_id = fs.get('FileSystemId')
                self._display_filesystem_info(fs)
                
                try:
                    policy = self.describe_filesystem_policy(fs_id)
                    if policy:
                        self._display_filesystem_policy(fs_id, policy)
                except Exception as e:
                    if self.debug:
                        print_red(f"Error getting policy for filesystem {fs_id}: {str(e)}")

                try:
                    self._display_mount_targets(fs_id)
                except Exception as e:
                    if self.debug:
                        print_red(f"Error getting mount targets for filesystem {fs_id}: {str(e)}")

            # Check access points
            try:
                access_points = self.describe_access_points()
                if access_points:
                    self._display_access_points(access_points)
            except Exception as e:
                if self.debug:
                    print_red(f"Error getting access points: {str(e)}")

            # Check replication configurations
            try:
                replication_configs = self.describe_replication_configurations()
                if replication_configs:
                    self._display_replication_configs(replication_configs)
            except Exception as e:
                if self.debug:
                    print_red(f"Error getting replication configs: {str(e)}")

        except Exception as e:
            print_red(f"Error enumerating EFS resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        if action == "efs:Describe*":
            print_yellow(f"\n[*] Found {action} permission - Full EFS access")
            self._handle_describe_filesystems(action)
            self._handle_describe_policy(action, resource)
            self._handle_describe_mount_targets(action, resource)
            self._handle_describe_security_groups(action, resource)
            self._handle_describe_access_points(action)
            self._handle_describe_replication(action)
            return

        # Handle specific Describe permissions
        if action == "efs:DescribeFileSystems":
            self._handle_describe_filesystems(action)
        elif action == "efs:DescribeFileSystemPolicy":
            self._handle_describe_policy(action, resource)
        elif action == "efs:DescribeMountTargets":
            self._handle_describe_mount_targets(action, resource)
        elif action == "efs:DescribeMountTargetSecurityGroups":
            self._handle_describe_security_groups(action, resource)
        elif action == "efs:DescribeAccessPoints":
            self._handle_describe_access_points(action)
        elif action == "efs:DescribeReplicationConfigurations":
            self._handle_describe_replication(action)

    def _handle_describe_filesystems(self, action):
        print_yellow(f"\n[*] Found {action} permission - Running 'describe_file_systems'")
        try:
            filesystems = self.describe_file_systems()
            if not filesystems:
                print_yellow("No EFS filesystems found.")
                return
            
            for fs in filesystems:
                self._display_filesystem_info(fs)
        except Exception as e:
            if self.debug:
                print_red(f"Error in filesystems handler: {str(e)}")
    
    def _handle_describe_policy(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Running 'describe_filesystem_policy'")
        try:
            if resource == '*':
                filesystems = self.describe_file_systems()
                for fs in filesystems:
                    fs_id = fs.get('FileSystemId')
                    policy = self.describe_filesystem_policy(fs_id)
                    if policy:
                        self._display_filesystem_policy(fs_id, policy)
            else:
                fs_id = resource.split('/')[-1]
                policy = self.describe_filesystem_policy(fs_id)
                if policy:
                    self._display_filesystem_policy(fs_id, policy)
                else:
                    print_yellow(f"No policy found for file system {fs_id}")
        except Exception as e:
            if self.debug:
                print_red(f"Error in policy handler: {str(e)}")
    
    def _handle_describe_mount_targets(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Running 'describe_mount_targets'")
        try:
            if resource == '*':
                filesystems = self.describe_file_systems()
                for fs in filesystems:
                    fs_id = fs.get('FileSystemId')
                    self._display_mount_targets(fs_id)
            else:
                fs_id = resource.split('/')[-1]
                self._display_mount_targets(fs_id)
        except Exception as e:
            if self.debug:
                print_red(f"Error in mount targets handler: {str(e)}")
    
    def _display_filesystem_info(self, fs):
        fs_id = fs.get('FileSystemId')
        print_yellow(f"\n[*] File System: {fs_id}")
        
        fs_data = [
            ['Name', fs.get('Name', 'N/A')],
            ['State', fs.get('LifeCycleState')],
            ['Size', f"{fs.get('SizeInBytes', {}).get('Value', 0)} bytes"],
            ['Creation Time', fs.get('CreationTime')],
            ['Encrypted', str(fs.get('Encrypted', False))],
            ['Performance Mode', fs.get('PerformanceMode')]
        ]
        print(tabulate(fs_data, tablefmt='plain'))

    def _handle_describe_security_groups(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Running 'describe_mount_target_security_groups'")
        try:
            if resource == '*':
                filesystems = self.describe_file_systems()
                for fs in filesystems:
                    fs_id = fs.get('FileSystemId')
                    mount_targets = self.describe_mount_targets(fs_id)
                    for mt in mount_targets:
                        self._display_security_groups(mt.get('MountTargetId'))
            else:
                mount_targets = self.describe_mount_targets(resource.split('/')[-1])
                for mt in mount_targets:
                    self._display_security_groups(mt.get('MountTargetId'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in security groups handler: {str(e)}")

    def _handle_describe_access_points(self, action):
        print_yellow(f"\n[*] Found {action} permission - Running 'describe_access_points'")
        try:
            access_points = self.describe_access_points()
            if access_points:
                self._display_access_points(access_points)
        except Exception as e:
            if self.debug:
                print_red(f"Error in access points handler: {str(e)}")

    def _handle_describe_replication(self, action):
        print_yellow(f"\n[*] Found {action} permission - Running 'describe_replication_configurations'")
        try:
            configs = self.describe_replication_configurations()
            if configs:
                self._display_replication_configs(configs)
        except Exception as e:
            if self.debug:
                print_red(f"Error in replication config handler: {str(e)}")

    def _display_filesystem_policy(self, fs_id, policy):
        print_yellow(f"\nFile System Policy for {fs_id}:")
        print(yaml.dump(policy))

    def _display_mount_targets(self, fs_id):
        mount_targets = self.describe_mount_targets(fs_id)
        if mount_targets:
            print_yellow("\nMount Targets:")

            table_data = []
            for mt in mount_targets:
                table_data.append([
                    mt.get('MountTargetId'),
                    mt.get('SubnetId'),
                    mt.get('IpAddress'),
                    mt.get('LifeCycleState')
                ])

            headers = ['Mount Target ID', 'Subnet ID', 'IP Address', 'State']
            print(tabulate(table_data, headers=headers, tablefmt='simple'))

    def _display_security_groups(self, mt_id):
        sg_ids = self.describe_mount_target_security_groups(mt_id)
        if sg_ids:
            print_yellow(f"\nSecurity Groups for Mount Target {mt_id}:")
            for sg_id in sg_ids:
                sg_info = self.describe_security_groups(sg_id)
                if sg_info:
                    # Basic security group info
                    sg_headers = ['Property', 'Value']
                    sg_data = [
                        ['Security Group ID', sg_info.get('GroupId')],
                        ['Name', sg_info.get('GroupName')],
                        ['Description', sg_info.get('Description')]
                    ]
                    print(tabulate(sg_data, headers=sg_headers, tablefmt='simple'))
    
                    # Inbound rules
                    if sg_info.get('IpPermissions'):
                        print_yellow("\nInbound Rules:")
                        inbound_data = []
                        rule_headers = ['Protocol', 'Port Range', 'Source/Destination']
                        
                        for rule in sg_info.get('IpPermissions'):
                            protocol = rule.get('IpProtocol', 'All')
                            if protocol == '-1':
                                protocol = 'All'
                            port_range = f"{rule.get('FromPort', 'All')}-{rule.get('ToPort', 'All')}"
                            if port_range == 'All-All':
                                port_range = 'All'
                            sources = ', '.join(ip['CidrIp'] for ip in rule.get('IpRanges', []))
                            inbound_data.append([protocol, port_range, sources])
                        
                        print(tabulate(inbound_data, headers=rule_headers, tablefmt='simple'))
    
                    # Outbound rules
                    if sg_info.get('IpPermissionsEgress'):
                        print_yellow("\nOutbound Rules:")
                        outbound_data = []
                        
                        for rule in sg_info.get('IpPermissionsEgress'):
                            protocol = rule.get('IpProtocol', 'All')
                            if protocol == '-1':
                                protocol = 'All'
                            port_range = f"{rule.get('FromPort', 'All')}-{rule.get('ToPort', 'All')}"
                            if port_range == 'All-All':
                                port_range = 'All'
                            destinations = ', '.join(ip['CidrIp'] for ip in rule.get('IpRanges', []))
                            outbound_data.append([protocol, port_range, destinations])
                        
                        print(tabulate(outbound_data, headers=rule_headers, tablefmt='simple'))

    def _display_access_points(self, access_points):
        print_yellow("\nAccess Points:")
        for ap in access_points:
            ap_data = [
                ['Access Point ID', ap.get('AccessPointId')],
                ['File System ID', ap.get('FileSystemId')],
                ['Root Directory', ap.get('RootDirectory', {}).get('Path')],
                ['Owner UID', ap.get('PosixUser', {}).get('Uid')],
                ['Owner GID', ap.get('PosixUser', {}).get('Gid')],
                ['State', ap.get('LifeCycleState')]
            ]
            print(tabulate(ap_data, tablefmt='plain'))

    def _display_replication_configs(self, configs):
        print_yellow("\nReplication Configurations:")
        print(yaml.dump(configs))

    # API wrapper methods
    def describe_file_systems(self):
        response = self.client.describe_file_systems()
        return response.get('FileSystems', [])

    def describe_filesystem_policy(self, fs_id):
        try:
            response = self.client.describe_file_system_policy(FileSystemId=fs_id)
            return response.get('Policy')
        except ClientError as e:
            if e.response['Error']['Code'] == 'PolicyNotFound':
                return None
            raise

    def describe_mount_targets(self, fs_id):
        response = self.client.describe_mount_targets(FileSystemId=fs_id)
        return response.get('MountTargets', [])

    def describe_mount_target_security_groups(self, mt_id):
        response = self.client.describe_mount_target_security_groups(MountTargetId=mt_id)
        return response.get('SecurityGroups', [])

    def describe_security_groups(self, group_id):
        response = self.ec2_client.describe_security_groups(GroupIds=[group_id])
        return response.get('SecurityGroups', [])[0] if response.get('SecurityGroups') else None

    def describe_access_points(self):
        response = self.client.describe_access_points()
        return response.get('AccessPoints', [])

    def describe_replication_configurations(self):
        response = self.client.describe_replication_configurations()
        return response.get('ReplicationConfigurations', [])