from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta
import boto3

class StepFunctionsService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'stepfunctions', debug)
        self.supported_actions = [
            "states:*",
            "states:List*",
            "states:Describe*",
            "states:ListStateMachines",
            "states:DescribeStateMachine",
            "states:ListStateMachineVersions",
            "states:ListStateMachineAliases",
            "states:DescribeStateMachineAlias",
            "states:ListExecutions",
            "states:DescribeExecution",
            "states:DescribeStateMachineForExecution"
        ]

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating Step Functions Resources")
        print_cyan("*" * 80)

        try:
            self._handle_list_state_machines("states:ListStateMachines", "*")
            self._handle_describe_state_machine("states:DescribeStateMachine", "*")
            self._handle_list_state_machine_versions("states:ListStateMachineVersions", "*")
            self._handle_list_state_machine_aliases("states:ListStateMachineAliases", "*")
            self._handle_describe_state_machine_alias("states:DescribeStateMachineAlias", "*")
            self._handle_list_executions("states:ListExecutions", "*")
            self._handle_describe_execution("states:DescribeExecution", "*")
            self._handle_describe_state_machine_for_execution("states:DescribeStateMachineForExecution", "*")
        except Exception as e:
            print_red(f"Error enumerating Step Functions resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        if "states:ListStateMachines" in action or "states:List*" in action or "states:*" in action:
            self._handle_list_state_machines(action, resource)
        elif "states:DescribeStateMachine" in action or "states:Describe*" in action or "states:*" in action:
            self._handle_describe_state_machine(action, resource)
        elif "states:ListStateMachineVersions" in action or "states:List*" in action or "states:*" in action:
            self._handle_list_state_machine_versions(action, resource)
        elif "states:ListStateMachineAliases" in action or "states:List*" in action or "states:*" in action:
            self._handle_list_state_machine_aliases(action, resource)
        elif "states:DescribeStateMachineAlias" in action or "states:Describe*" in action or "states:*" in action:
            self._handle_describe_state_machine_alias(action, resource)
        elif "states:ListExecutions" in action or "states:List*" in action or "states:*" in action:
            self._handle_list_executions(action, resource)
        elif "states:DescribeExecution" in action or "states:Describe*" in action or "states:*" in action:
            self._handle_describe_execution(action, resource)
        elif "states:DescribeStateMachineForExecution" in action or "states:Describe*" in action or "states:*" in action:
            self._handle_describe_state_machine_for_execution(action, resource)

    def _handle_list_state_machines(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing state machines")
        try:
            state_machines = self.list_state_machines()
            if state_machines:
                print_yellow("\nAvailable State Machines:")
                for sm in state_machines:
                    print(f"State Machine ARN: {sm.get('stateMachineArn')}")
                    print(f"Name: {sm.get('name')}")
                    print(f"Type: {sm.get('type')}")
                    print("---")
        except Exception as e:
            if self.debug:
                print_red(f"Error in list state machines handler: {str(e)}")

    def _handle_describe_state_machine(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Describing state machine")
        try:
            if resource != "*" and resource.startswith("arn:"):
                sm = self.describe_state_machine(resource)
                if sm:
                    print_yellow(f"\nState Machine Details for: {resource}")
                    sm_data = [[k, v] for k, v in sm.items()]
                    print(tabulate(sm_data, headers=['Property', 'Value'], tablefmt='simple'))
            else:
                state_machines = self.list_state_machines()
                for sm in state_machines:
                    sm_arn = sm.get('stateMachineArn')
                    details = self.describe_state_machine(sm_arn)
                    if details:
                        print_yellow(f"\nState Machine Details for: {sm_arn}")
                        sm_data = [[k, v] for k, v in details.items()]
                        print(tabulate(sm_data, headers=['Property', 'Value'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in describe state machine handler: {str(e)}")

    def _handle_list_state_machine_versions(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing state machine versions")
        try:
            if resource != "*" and resource.startswith("arn:"):
                versions = self.list_state_machine_versions(resource)
                if versions:
                    print_yellow(f"\nVersions for state machine: {resource}")
                    for version in versions:
                        print(f"Version ARN: {version.get('stateMachineVersionArn')}")
                        print(f"Version: {version.get('version')}")
                        print("---")
            else:
                state_machines = self.list_state_machines()
                for sm in state_machines:
                    sm_arn = sm.get('stateMachineArn')
                    versions = self.list_state_machine_versions(sm_arn)
                    if versions:
                        print_yellow(f"\nVersions for state machine: {sm_arn}")
                        for version in versions:
                            print(f"Version ARN: {version.get('stateMachineVersionArn')}")
                            print(f"Version: {version.get('version')}")
                            print("---")
        except Exception as e:
            if self.debug:
                print_red(f"Error in list state machine versions handler: {str(e)}")

    def _handle_list_state_machine_aliases(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing state machine aliases")
        try:
            if resource != "*" and resource.startswith("arn:"):
                aliases = self.list_state_machine_aliases(resource)
                if aliases:
                    print_yellow(f"\nAliases for state machine: {resource}")
                    for alias in aliases:
                        print(f"Alias ARN: {alias.get('stateMachineAliasArn')}")
                        print(f"Name: {alias.get('name')}")
                        print("---")
            else:
                state_machines = self.list_state_machines()
                for sm in state_machines:
                    sm_arn = sm.get('stateMachineArn')
                    aliases = self.list_state_machine_aliases(sm_arn)
                    if aliases:
                        print_yellow(f"\nAliases for state machine: {sm_arn}")
                        for alias in aliases:
                            print(f"Alias ARN: {alias.get('stateMachineAliasArn')}")
                            print(f"Name: {alias.get('name')}")
                            print("---")
        except Exception as e:
            if self.debug:
                print_red(f"Error in list state machine aliases handler: {str(e)}")

    def _handle_describe_state_machine_alias(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Describing state machine alias")
        try:
            if resource != "*" and resource.startswith("arn:"):
                alias = self.describe_state_machine_alias(resource)
                if alias:
                    print_yellow(f"\nAlias Details for: {resource}")
                    alias_data = [[k, v] for k, v in alias.items()]
                    print(tabulate(alias_data, headers=['Property', 'Value'], tablefmt='simple'))
            else:
                state_machines = self.list_state_machines()
                for sm in state_machines:
                    sm_arn = sm.get('stateMachineArn')
                    aliases = self.list_state_machine_aliases(sm_arn)
                    for alias in aliases:
                        alias_arn = alias.get('stateMachineAliasArn')
                        details = self.describe_state_machine_alias(alias_arn)
                        if details:
                            print_yellow(f"\nAlias Details for: {alias_arn}")
                            alias_data = [[k, v] for k, v in details.items()]
                            print(tabulate(alias_data, headers=['Property', 'Value'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in describe state machine alias handler: {str(e)}")

    def _handle_list_executions(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing executions")
        try:
            if resource != "*" and resource.startswith("arn:"):
                executions = self.list_executions(resource)
                if executions:
                    print_yellow(f"\nExecutions for state machine: {resource}")
                    for execution in executions:
                        print(f"Execution ARN: {execution.get('executionArn')}")
                        print(f"Status: {execution.get('status')}")
                        print(f"Start Date: {execution.get('startDate')}")
                        print("---")
            else:
                state_machines = self.list_state_machines()
                for sm in state_machines:
                    sm_arn = sm.get('stateMachineArn')
                    executions = self.list_executions(sm_arn)
                    if executions:
                        print_yellow(f"\nExecutions for state machine: {sm_arn}")
                        for execution in executions:
                            print(f"Execution ARN: {execution.get('executionArn')}")
                            print(f"Status: {execution.get('status')}")
                            print(f"Start Date: {execution.get('startDate')}")
                            print("---")
        except Exception as e:
            if self.debug:
                print_red(f"Error in list executions handler: {str(e)}")

    def _handle_describe_execution(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Describing execution")
        try:
            if resource != "*" and resource.startswith("arn:"):
                execution = self.describe_execution(resource)
                if execution:
                    print_yellow(f"\nExecution Details for: {resource}")
                    exec_data = [[k, v] for k, v in execution.items()]
                    print(tabulate(exec_data, headers=['Property', 'Value'], tablefmt='simple'))
            else:
                state_machines = self.list_state_machines()
                for sm in state_machines:
                    sm_arn = sm.get('stateMachineArn')
                    executions = self.list_executions(sm_arn)
                    for execution in executions:
                        execution_arn = execution.get('executionArn')
                        details = self.describe_execution(execution_arn)
                        if details:
                            print_yellow(f"\nExecution Details for: {execution_arn}")
                            exec_data = [[k, v] for k, v in details.items()]
                            print(tabulate(exec_data, headers=['Property', 'Value'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in describe execution handler: {str(e)}")

    def _handle_describe_state_machine_for_execution(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Describing state machine for execution")
        try:
            if resource != "*" and resource.startswith("arn:"):
                sm = self.describe_state_machine_for_execution(resource)
                if sm:
                    print_yellow(f"\nState Machine Details for execution: {resource}")
                    sm_data = [[k, v] for k, v in sm.items()]
                    print(tabulate(sm_data, headers=['Property', 'Value'], tablefmt='simple'))
            else:
                state_machines = self.list_state_machines()
                for sm in state_machines:
                    sm_arn = sm.get('stateMachineArn')
                    executions = self.list_executions(sm_arn)
                    for execution in executions:
                        execution_arn = execution.get('executionArn')
                        details = self.describe_state_machine_for_execution(execution_arn)
                        if details:
                            print_yellow(f"\nState Machine Details for execution: {execution_arn}")
                            sm_data = [[k, v] for k, v in details.items()]
                            print(tabulate(sm_data, headers=['Property', 'Value'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in describe state machine for execution handler: {str(e)}")

    # API wrapper methods
    def list_state_machines(self):
        response = self.client.list_state_machines()
        return response.get('stateMachines', [])

    def describe_state_machine(self, state_machine_arn):
        response = self.client.describe_state_machine(stateMachineArn=state_machine_arn)
        return response

    def list_state_machine_versions(self, state_machine_arn):
        response = self.client.list_state_machine_versions(stateMachineArn=state_machine_arn)
        return response.get('stateMachineVersions', [])

    def list_state_machine_aliases(self, state_machine_arn):
        response = self.client.list_state_machine_aliases(stateMachineArn=state_machine_arn)
        return response.get('stateMachineAliases', [])

    def describe_state_machine_alias(self, state_machine_alias_arn):
        response = self.client.describe_state_machine_alias(stateMachineAliasArn=state_machine_alias_arn)
        return response

    def list_executions(self, state_machine_arn):
        response = self.client.list_executions(stateMachineArn=state_machine_arn)
        return response.get('executions', [])

    def describe_execution(self, execution_arn):
        response = self.client.describe_execution(executionArn=execution_arn)
        return response

    def describe_state_machine_for_execution(self, execution_arn):
        response = self.client.describe_state_machine_for_execution(executionArn=execution_arn)
        return response
