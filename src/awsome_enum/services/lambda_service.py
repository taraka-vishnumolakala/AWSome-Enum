import yaml
from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta

class LambdaService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'lambda', debug)
        self.supported_actions = [
            "lambda:*",
            "lambda:ListFunctions",
            "lambda:GetFunction",
            "lambda:GetFunctionUrlConfig",
            "lambda:GetFunctionConfiguration"
        ]
    
    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating Lambda Resources")
        print_cyan("*" * 80)
        
        try:
            functions = self.list_functions()
            if not functions:
                print_yellow("No Lambda functions found.")
                return
    
            for function in functions:
                function_name = function.get('FunctionName')
                
                try:
                    detailed_info = self.get_function(function_name)
                    if detailed_info:
                        self._display_detailed_function_info(function_name)
                except Exception as e:
                    if self.debug:
                        print_red(f"Error getting details for function {function_name}: {str(e)}")
                
                try:
                    url_config = self.get_function_url_config(function_name)
                    if url_config:
                        self._display_function_url_config(function_name)
                except Exception as e:
                    if self.debug:
                        print_red(f"Error getting URL config for function {function_name}: {str(e)}")
    
        except Exception as e:
            print_red(f"Error enumerating Lambda resources: {str(e)}")
    
    def handle_permission_action(self, action, resource):
        if "lambda:ListFunctions" == action or "lambda:*" in action:
            self._handle_list_functions(action)
        elif "lambda:GetFunction" == action or "lambda:*" in action:
            self._handle_get_function(action, resource)            
        elif "lambda:GetFunctionUrlConfig" == action or "lambda:*" in action:
            self._handle_get_function_url(action, resource)
        elif "lambda:GetFunctionConfiguration" == action or "lambda:*" in action:
            self._handle_get_function_configuration(action, resource)

    def _handle_list_functions(self, action):
        print_yellow(f"\n[*] Found {action} permission - Listing all functions")
        functions = self.list_functions()
        if not functions:
            print_yellow("No Lambda functions found.")
            return
        
        for function in functions:
            self._display_basic_function_info(function)

    def _display_basic_function_info(self, function):
        print_yellow(f"\n[*] Function: {function.get('FunctionName')}")
        
        basic_data = [
            ['ARN', function.get('FunctionArn')],
            ['Runtime', function.get('Runtime')],
            ['Handler', function.get('Handler')],
            ['Role', function.get('Role')],
            ['Last Modified', function.get('LastModified')]
        ]
        print(tabulate(basic_data, tablefmt='plain'))

    def _handle_get_function(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission")
        
        try:
            if resource == '*':
                functions = self.list_functions()
                for function in functions:
                    self._display_detailed_function_info(function['FunctionName'])
            else:
                function_name = resource.split(':')[-1] if ':' in resource else resource
                self._display_detailed_function_info(function_name)
        except Exception as e:
            if self.debug:
                print_red(f"Error in get function handler: {str(e)}")

    def _display_detailed_function_info(self, function_name):
        try:
            detailed_info = self.get_function(function_name)
            if not detailed_info:
                return

            config = detailed_info.get('Configuration', {})
            print_yellow(f"\n[*] Detailed information for {function_name}:")
            
            function_data = [
                ['Runtime', config.get('Runtime')],
                ['Handler', config.get('Handler')],
                ['Role', config.get('Role')],
                ['State', config.get('State', 'Unknown')],
                ['Memory', f"{config.get('MemorySize')} MB"],
                ['Timeout', f"{config.get('Timeout')} seconds"],
                ['Last Modified', config.get('LastModified')],
                ['Architecture', ', '.join(config.get('Architectures', []))]
            ]
            print(tabulate(function_data, tablefmt='plain'))

            if code_info := detailed_info.get('Code', {}):
                print_yellow("\nCode Location:")
                print(code_info.get('Location', 'N/A'))

            if logging_config := config.get('LoggingConfig'):
                print_yellow("\nLogging Configuration:")
                print(f"Log Group: {logging_config.get('LogGroup')}")
                print(f"Log Format: {logging_config.get('LogFormat')}")

            if config.get('Runtime', '').startswith('python2'):
                print_red("\n[!] Warning: Function uses deprecated Python 2.x runtime")
            if config.get('Timeout', 0) > 600:
                print_yellow("\n[!] Note: Function has a high timeout value")

        except Exception as e:
            if self.debug:
                print_red(f"Error getting details for function {function_name}: {str(e)}")

    def _handle_get_function_url(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Checking URL configuration")
        
        try:
            if resource == '*':
                functions = self.list_functions()
                for function in functions:
                    self._display_function_url_config(function['FunctionName'])
            else:
                function_name = resource.split(':')[-1] if ':' in resource else resource
                self._display_function_url_config(function_name)
        except Exception as e:
            if self.debug:
                print_red(f"Error in function URL handler: {str(e)}")

    def _display_function_url_config(self, function_name):
        try:
            url_config = self.get_function_url_config(function_name)
            if url_config:
                print_yellow(f"\nURL Configuration for {function_name}:")
                url_data = [
                    ['URL', url_config.get('FunctionUrl')],
                    ['Auth Type', url_config.get('AuthType')],
                    ['Invoke Mode', url_config.get('InvokeMode')]
                ]
                print(tabulate(url_data, tablefmt='plain'))

                if url_config.get('AuthType') == 'NONE':
                    print_red("\n[!] Warning: Function URL has no authentication!")
        except Exception as e:
            if self.debug:
                print_red(f"Error getting URL config for {function_name}: {str(e)}")

    def _handle_get_function_configuration(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Checking function configuration")
        
        try:
            if resource == '*':
                functions = self.list_functions()
                for function in functions:
                    self._display_function_configuration(function['FunctionName'])
            else:
                function_name = resource.split(':')[-1] if ':' in resource else resource
                self._display_function_configuration(function_name)
        except Exception as e:
            if self.debug:
                print_red(f"Error in function configuration handler: {str(e)}")

    def _display_function_configuration(self, function_name):
        try:
            config = self.get_function_configuration(function_name)
            if config:
                print_yellow(f"\nConfiguration for {function_name}:")
                config_data = [
                    ['Runtime', config.get('Runtime')],
                    ['Handler', config.get('Handler')],
                    ['Role', config.get('Role')],
                    ['Environment', str(config.get('Environment', {}).get('Variables', {}))],
                    ['Layers', ', '.join(layer['Arn'] for layer in config.get('Layers', []))],
                    ['VPC Config', str(config.get('VpcConfig', {}))],
                    ['Package Type', config.get('PackageType')],
                    ['Ephemeral Storage', f"{config.get('EphemeralStorage', {}).get('Size', 0)} MB"],
                    ['Code Signing', str(config.get('CodeSigningConfig', {}))]
                ]
                print(tabulate(config_data, tablefmt='simple'))

                # Security warnings
                if config.get('Environment', {}).get('Variables'):
                    print_yellow("\n[!] Function has environment variables configured")
                if config.get('VpcConfig', {}).get('SubnetIds'):
                    print_yellow("\n[!] Function is VPC-enabled")
                if not config.get('CodeSigningConfig'):
                    print_red("\n[!] Warning: No code signing configuration found")
        except Exception as e:
            if self.debug:
                print_red(f"Error getting configuration for {function_name}: {str(e)}")

    # Wrapper methods for Lambda API calls
    def list_functions(self):
        response = self.client.list_functions()
        return response.get('Functions', [])

    def get_function(self, function_name):
        return self.client.get_function(FunctionName=function_name)

    def get_function_url_config(self, function_name):
        try:
            return self.client.get_function_url_config(FunctionName=function_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return None
            raise

    def get_function_configuration(self, function_name):
        try:
            return self.client.get_function_configuration(FunctionName=function_name)
        except ClientError as e:
            if self.debug:
                print_red(f"Error getting function configuration: {str(e)}")
            return None