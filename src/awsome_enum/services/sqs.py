from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta
import boto3

class SQSService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'sqs', debug)
        self.supported_actions = [
            "sqs:*",
            "sqs:ListQueues",
            "sqs:GetQueueAttributes",
            "sqs:ReceiveMessage",
            "sqs:SendMessage"
        ]

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating SQS Resources")
        print_cyan("*" * 80)

        try:
            self._handle_list_queues("sqs:ListQueues", "*")
            self._handle_get_queue_attributes("sqs:GetQueueAttributes", "*")
            self._handle_receive_message("sqs:ReceiveMessage", "*")
            self._handle_send_message("sqs:SendMessage", "*")
        except Exception as e:
            print_red(f"Error enumerating SQS resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        if "sqs:ListQueues" == action or "sqs:*" == action:
            self._handle_list_queues(action, resource)
        elif "sqs:GetQueueAttributes" == action or "sqs:*" == action:
            self._handle_get_queue_attributes(action, resource)
        elif "sqs:ReceiveMessage" == action or "sqs:*" == action:
            self._handle_receive_message(action, resource)
        elif "sqs:SendMessage" == action or "sqs:*" == action:
            self._handle_send_message(action, resource)

    def _handle_list_queues(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing queues")
        try:
            queues = self.list_queues()
            if queues:
                print_yellow("\nAvailable Queues:")
                for queue_url in queues:
                    print_green(f"Queue URL: {queue_url}")
                    # Try to get queue attributes for each queue
                    self._handle_get_queue_attributes(action, queue_url)
        except Exception as e:
            if self.debug:
                print_red(f"Error in list queues handler: {str(e)}")

    def _handle_get_queue_attributes(self, action, queue_url):
        print_yellow(f"\n[*] Found {action} permission - Getting queue attributes")
        try:
            attributes = self.get_queue_attributes(queue_url)
            if attributes:
                print_yellow(f"\nAttributes for queue: {queue_url}")
                attr_data = [[k, v] for k, v in attributes.items()]
                print(tabulate(attr_data, headers=['Attribute', 'Value'], tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in get queue attributes handler: {str(e)}")

    def _handle_receive_message(self, action, queue_url):
        print_yellow(f"\n[*] Found {action} permission - Receiving messages")
        try:
            messages = self.receive_message(queue_url)
            if messages:
                print_yellow(f"\nReceived messages from queue: {queue_url}")
                for msg in messages:
                    msg_data = [
                        ['MessageId', msg.get('MessageId')],
                        ['Body', msg.get('Body')],
                        ['MD5 of Body', msg.get('MD5OfBody')]
                    ]
                    print(tabulate(msg_data, tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in receive message handler: {str(e)}")

    def _handle_send_message(self, action, queue_url, message_body="Test message"):
        print_yellow(f"\n[*] Found {action} permission - Sending message")
        try:
            response = self.send_message(queue_url, message_body)
            if response:
                print_green(f"Message sent successfully to {queue_url}")
                print_green(f"MessageId: {response.get('MessageId')}")
        except Exception as e:
            if self.debug:
                print_red(f"Error in send message handler: {str(e)}")

    # API wrapper methods
    def list_queues(self):
        response = self.client.list_queues()
        return response.get('QueueUrls', [])

    def get_queue_attributes(self, queue_url):
        response = self.client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['All']
        )
        return response.get('Attributes', {})

    def receive_message(self, queue_url):
        response = self.client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10
        )
        return response.get('Messages', [])

    def send_message(self, queue_url, message_body):
        response = self.client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )
        return response
