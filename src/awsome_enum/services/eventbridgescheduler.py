from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta
import boto3

class EventBridgeSchedulerService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'scheduler', debug)
        self.supported_actions = [
            "scheduler:*",
            "scheduler:ListSchedules",
            "scheduler:ListScheduleGroups",
            "scheduler:GetSchedule",
            "scheduler:GetScheduleGroup",
            "scheduler:ListTagsForResource"
        ]

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating EventBridge Scheduler Resources")
        print_cyan("*" * 80)

        try:
            self._handle_list_schedules("scheduler:ListSchedules", "*")
            self._handle_list_schedule_groups("scheduler:ListScheduleGroups", "*")
        except Exception as e:
            print_red(f"Error enumerating EventBridge Scheduler resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        if "scheduler:ListSchedules" == action or "scheduler:List*" == action or "scheduler:*" == action:
            self._handle_list_schedules(action, resource)
        elif "scheduler:ListScheduleGroups" == action or "scheduler:List*" == action or "scheduler:*" == action:
            self._handle_list_schedule_groups(action, resource)
        elif "scheduler:GetSchedule" == action or "scheduler:Get*" == action or "scheduler:*" == action:
            self._handle_get_schedule(action, resource)
        elif "scheduler:GetScheduleGroup" == action or "scheduler:Get*" == action or "scheduler:*" == action:
            self._handle_get_schedule_group(action, resource)
        elif "scheduler:ListTagsForResource" == action or "scheduler:List*" == action or "scheduler:*" == action:
            self._handle_list_tags(action, resource)

    def _handle_list_schedules(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing schedules")
        try:
            schedules = self.list_schedules()
            if schedules:
                print_yellow("\nAvailable Schedules:")
                schedule_data = [[s.get('Name'), s.get('GroupName'), s.get('State')] for s in schedules]
                print(tabulate(schedule_data, 
                             headers=['Schedule Name', 'Group Name', 'State'], 
                             tablefmt='simple'))
                # Try to get details for each schedule
                for schedule in schedules:
                    self._handle_get_schedule(action, schedule.get('Name'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in list schedules handler: {str(e)}")

    def _handle_list_schedule_groups(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing schedule groups")
        try:
            groups = self.list_schedule_groups()
            if groups:
                print_yellow("\nSchedule Groups:")
                group_data = [[g.get('Name'), g.get('Arn')] for g in groups]
                print(tabulate(group_data, 
                             headers=['Group Name', 'ARN'], 
                             tablefmt='simple'))
                # Try to get details and tags for each group
                for group in groups:
                    self._handle_get_schedule_group(action, group.get('Name'))
                    self._handle_list_tags(action, group.get('Arn'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in list schedule groups handler: {str(e)}")

    def _handle_get_schedule(self, action, schedule_name):
        print_yellow(f"\n[*] Found {action} permission - Getting schedule details: {schedule_name}")
        try:
            schedule = self.get_schedule(schedule_name)
            if schedule:
                print_yellow(f"\nSchedule Details for {schedule_name}:")
                details = [
                    ['Name', schedule.get('Name')],
                    ['Group Name', schedule.get('GroupName')],
                    ['State', schedule.get('State')],
                    ['Target', str(schedule.get('Target'))],
                    ['Schedule Expression', schedule.get('ScheduleExpression')]
                ]
                print(tabulate(details, tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in get schedule handler: {str(e)}")

    def _handle_get_schedule_group(self, action, group_name):
        print_yellow(f"\n[*] Found {action} permission - Getting schedule group details: {group_name}")
        try:
            group = self.get_schedule_group(group_name)
            if group:
                print_yellow(f"\nSchedule Group Details for {group_name}:")
                details = [
                    ['Name', group.get('Name')],
                    ['ARN', group.get('Arn')],
                    ['Creation Date', str(group.get('CreationDate'))]
                ]
                print(tabulate(details, tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in get schedule group handler: {str(e)}")

    def _handle_list_tags(self, action, resource_arn):
        print_yellow(f"\n[*] Found {action} permission - Listing tags for: {resource_arn}")
        try:
            tags = self.list_tags_for_resource(resource_arn)
            if tags:
                print_yellow(f"\nTags:")
                tags_data = [[k, v] for k, v in tags.items()]
                print(tabulate(tags_data, headers=['Key', 'Value'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in list tags handler: {str(e)}")

    # API wrapper methods
    def list_schedules(self):
        response = self.client.list_schedules()
        return response.get('Schedules', [])

    def list_schedule_groups(self):
        response = self.client.list_schedule_groups()
        return response.get('ScheduleGroups', [])

    def get_schedule(self, name):
        response = self.client.get_schedule(Name=name)
        return response

    def get_schedule_group(self, name):
        response = self.client.get_schedule_group(Name=name)
        return response

    def list_tags_for_resource(self, resource_arn):
        response = self.client.list_tags_for_resource(ResourceArn=resource_arn)
        return response.get('Tags', {})
