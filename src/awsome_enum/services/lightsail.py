import yaml
from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta

class LightsailService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'lightsail', debug)
        self.supported_actions = [
            "lightsail:GetInstances", 
            "lightsail:GetRelationalDatabases"
        ]
    
    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating Lightsail Resources")
        print_cyan("*" * 80)
        
        try:
            self._list_and_display_instances()
            self._list_and_display_databases()
        except Exception as e:
            print_red(f"Error enumerating Lightsail resources: {str(e)}")
    
    def handle_permission_action(self, action, resource):
        if "lightsail:GetInstances" in action:
            print_yellow(f"\n[*] Found {action} permission - Listing all instances:\n")
            self._list_and_display_instances()
        elif "lightsail:GetRelationalDatabases" in action:
            print_yellow(f"\n[*] Found {action} permission - Listing all databases:\n")
            self._list_and_display_databases()
    
    def _list_and_display_instances(self):
        try:
            instances = self.get_instances()
            if not instances:
                print_yellow("No Lightsail instances found.")
                return

            instance_data = []
            for instance in instances:
                instance_data.append([
                    instance.get('name'),
                    instance.get('state', {}).get('name'),
                    instance.get('publicIpAddress', 'N/A'),
                    instance.get('privateIpAddress'),
                    instance.get('username'),
                    instance.get('sshKeyName'),
                    instance.get('blueprintName')
                ])

                print_yellow(f"\n[*] Instance Details for {instance.get('name')}:")
                print(tabulate(
                    instance_data,
                    headers=['Name', 'State', 'Public IP', 'Private IP', 'Username', 'SSH Key', 'OS'],
                    tablefmt='plain'
                ))

                # Display open ports if any
                ports = instance.get('networking', {}).get('ports', [])
                if ports:
                    print_yellow(f"\n[*] Open ports for instance {instance['name']}:")
                    port_data = [[
                        f"{p['fromPort']}-{p['toPort']}", 
                        p['protocol'],
                        p['accessFrom']
                    ] for p in ports]
                    print(tabulate(
                        port_data,
                        headers=['Port Range', 'Protocol', 'Access From'],
                        tablefmt='plain'
                    ))

        except Exception as e:
            print_red(f"Error listing instances: {str(e)}")

    def _list_and_display_databases(self):
        try:
            databases = self.get_relational_databases()
            if not databases:
                print_yellow("No Lightsail databases found.")
                return

            for db in databases:
                print_yellow(f"\n[*] Database Details for {db.get('name')}:")
                
                db_data = [
                    ['Name', db.get('name')],
                    ['Engine', f"{db.get('engine')} {db.get('engineVersion')}"],
                    ['State', db.get('state')],
                    ['Master Username', db.get('masterUsername')],
                    ['Database Name', db.get('masterDatabaseName')],
                    ['Endpoint', f"{db.get('masterEndpoint', {}).get('address')}:{db.get('masterEndpoint', {}).get('port')}"],
                    ['Publicly Accessible', str(db.get('publiclyAccessible'))],
                    ['CPU Count', str(db.get('hardware', {}).get('cpuCount'))],
                    ['RAM (GB)', str(db.get('hardware', {}).get('ramSizeInGb'))],
                    ['Disk Size (GB)', str(db.get('hardware', {}).get('diskSizeInGb'))]
                ]

                print(tabulate(db_data, tablefmt='plain'))

                # Print security warnings
                if db.get('publiclyAccessible'):
                    print_red("\n[!] Warning: Database is publicly accessible!")

        except Exception as e:
            print_red(f"Error listing databases: {str(e)}")

    # Wrapper methods for Lightsail API calls
    def get_instances(self):
        response = self.client.get_instances()
        return response.get('instances', [])
    
    def get_relational_databases(self):
        response = self.client.get_relational_databases()
        return response.get('relationalDatabases', [])