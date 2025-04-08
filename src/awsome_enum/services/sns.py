from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta
import boto3

class SNSService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'sns', debug)
        self.supported_actions = [
            "sns:*",
            "sns:ListTopics",
            "sns:ListSubscriptions",
            "sns:ListSubscriptionsByTopic"
        ]

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating SNS Resources")
        print_cyan("*" * 80)

        try:
            self._handle_list_topics("sns:ListTopics", "*")
            self._handle_list_subscriptions("sns:ListSubscriptions", "*")
        except Exception as e:
            print_red(f"Error enumerating SNS resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        if "sns:ListTopics" == action or "sns:*" == action:
            self._handle_list_topics(action, resource)
        elif "sns:ListSubscriptions" == action or "sns:*" == action:
            self._handle_list_subscriptions(action, resource)
        elif "sns:ListSubscriptionsByTopic" == action or "sns:*" == action:
            self._handle_list_subscriptions_by_topic(action, resource)

    def _handle_list_topics(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing topics")
        try:
            topics = self.list_topics()
            if topics:
                print_yellow("\nAvailable Topics:")
                topics_data = [[topic.get('TopicArn')] for topic in topics]
                print(tabulate(topics_data, headers=['Topic ARN'], tablefmt='simple'))
                # Try to get subscriptions for each topic
                for topic in topics:
                    self._handle_list_subscriptions_by_topic(action, topic.get('TopicArn'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in list topics handler: {str(e)}")

    def _handle_list_subscriptions(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing subscriptions")
        try:
            subscriptions = self.list_subscriptions()
            if subscriptions:
                print_yellow("\nSubscriptions:")
                subs_data = [[s.get('SubscriptionArn'), s.get('TopicArn'), s.get('Protocol'), s.get('Endpoint')] 
                            for s in subscriptions]
                print(tabulate(subs_data, 
                             headers=['Subscription ARN', 'Topic ARN', 'Protocol', 'Endpoint'], 
                             tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in list subscriptions handler: {str(e)}")

    def _handle_list_subscriptions_by_topic(self, action, topic_arn):
        print_yellow(f"\n[*] Found {action} permission - Listing subscriptions for topic: {topic_arn}")
        try:
            subscriptions = self.list_subscriptions_by_topic(topic_arn)
            if subscriptions:
                print_yellow(f"\nSubscriptions for topic {topic_arn}:")
                subs_data = [[s.get('SubscriptionArn'), s.get('Protocol'), s.get('Endpoint')] 
                            for s in subscriptions]
                print(tabulate(subs_data, 
                             headers=['Subscription ARN', 'Protocol', 'Endpoint'], 
                             tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in list subscriptions by topic handler: {str(e)}")

    # API wrapper methods
    def list_topics(self):
        response = self.client.list_topics()
        return response.get('Topics', [])

    def list_subscriptions(self):
        response = self.client.list_subscriptions()
        return response.get('Subscriptions', [])

    def list_subscriptions_by_topic(self, topic_arn):
        response = self.client.list_subscriptions_by_topic(
            TopicArn=topic_arn
        )
        return response.get('Subscriptions', [])
