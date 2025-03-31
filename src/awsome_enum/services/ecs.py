from tabulate import tabulate
from .aws_service_interface import AWSServiceInterface
from botocore.exceptions import ClientError
from ..utils import print_cyan, print_yellow, print_red, print_green, print_magenta

class ECSService(AWSServiceInterface):
    def __init__(self, session=None, debug=False):
        super().__init__(session, 'ecs', debug)
        self.supported_actions = [
            "ecs:*",
            "ecs:ListClusters",
            "ecs:DescribeClusters",
            "ecs:ListContainerInstances",
            "ecs:DescribeContainerInstances",
            "ecs:ListServices",
            "ecs:DescribeServices",
            "ecs:DescribeTaskSets",
            "ecs:ListTaskDefinitionFamilies",
            "ecs:ListTaskDefinitions",
            "ecs:ListTasks",
            "ecs:DescribeTasks",
            "ecs:DescribeTaskDefinition"
        ]

    def enumerate(self):
        print_cyan("\n" + "*" * 80)
        print_cyan("Enumerating ECS Resources")
        print_cyan("*" * 80)

        try:
            self._handle_list_clusters("ecs:ListClusters", "*")
            self._handle_list_task_definitions("ecs:ListTaskDefinitions", "*")
            self._handle_list_task_definition_families("ecs:ListTaskDefinitionFamilies", "*")
            self._handle_list_container_instances("ecs:ListContainerInstances", "*")
            self._handle_list_services("ecs:ListServices", "*")
            self._handle_list_tasks("ecs:ListTasks", "*")
            self._handle_describe_task_sets("ecs:DescribeTaskSets", "*")
        except Exception as e:
            print_red(f"Error enumerating ECS resources: {str(e)}")

    def handle_permission_action(self, action, resource):
        if "ecs:ListClusters" == action or "ecs:*" == action:
            self._handle_list_clusters(action, resource)
        elif "ecs:DescribeClusters" == action or "ecs:*" == action:
            self._handle_describe_clusters(action, resource)
        elif "ecs:ListContainerInstances" == action or "ecs:*" == action:
            self._handle_list_container_instances(action, resource)
        elif "ecs:ListServices" == action or "ecs:*" == action:
            self._handle_list_services(action, resource)
        elif "ecs:DescribeServices" == action or "ecs:*" == action:
            self._handle_describe_services(action, resource)
        elif "ecs:DescribeTaskSets" == action or "ecs:*" == action:
            self._handle_describe_task_sets(action, resource)
        elif "ecs:ListTaskDefinitions" == action or "ecs:*" == action:
            self._handle_list_task_definitions(action, resource)
        elif "ecs:DescribeTaskDefinition" == action or "ecs:*" == action:
            self._handle_describe_task_definition(action, resource)
        elif "ecs:ListTasks" == action or "ecs:*" == action:
            self._handle_list_tasks(action, resource)

    def _handle_list_clusters(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing clusters")
        try:
            clusters = self.list_clusters()
            if clusters:
                for cluster_arn in clusters:
                    cluster_name = cluster_arn.split('/')[-1]
                    self._handle_describe_clusters("ecs:DescribeClusters", cluster_name)
            else:
                print_yellow("No clusters found.")
        except Exception as e:
            if self.debug:
                print_red(f"Error in clusters handler: {str(e)}")

    def _handle_describe_clusters(self, action, resource):
        try:
            clusters = self.describe_clusters([resource])
            if clusters:
                for cluster in clusters:
                    print_yellow(f"\n[*] Cluster: {cluster.get('clusterName')}")
                    cluster_data = [
                        ['ARN', cluster.get('clusterArn')],
                        ['Status', cluster.get('status')],
                        ['Running Tasks', cluster.get('runningTasksCount')],
                        ['Pending Tasks', cluster.get('pendingTasksCount')],
                        ['Active Services', cluster.get('activeServicesCount')],
                        ['Container Instances', cluster.get('registeredContainerInstancesCount')]
                    ]
                    print(tabulate(cluster_data, tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in describe clusters handler: {str(e)}")

    def _handle_list_services(self, action, cluster):
        print_yellow(f"\n[*] Found {action} permission - Listing services for cluster {cluster}")
        try:
            services = self.list_services(cluster)
            if services:
                # Only call describe_services if we have the permission
                self._handle_describe_services("ecs:DescribeServices", cluster)
        except Exception as e:
            if self.debug:
                print_red(f"Error in services handler: {str(e)}")

    def _handle_list_task_definitions(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing task definitions")
        try:
            task_defs = self.list_task_definitions()
            if task_defs:
                for task_def_arn in task_defs:
                    task_def = task_def_arn.split('/')[-1]
                    self._handle_describe_task_definition("ecs:DescribeTaskDefinition", task_def)
        except Exception as e:
            if self.debug:
                print_red(f"Error in task definitions handler: {str(e)}")

    def _handle_describe_task_definition(self, action, task_def):
        try:
            task_def_details = self.describe_task_definition(task_def)
            if task_def_details:
                print_yellow(f"\nTask Definition: {task_def_details.get('family')}:{task_def_details.get('revision')}")
                for container in task_def_details.get('containerDefinitions', []):
                    print_yellow(f"\nContainer: {container.get('name')}")
                    if env_vars := container.get('environment', []):
                        print_yellow("Environment Variables:")
                        for env in env_vars:
                            print(f"{env.get('name')}: {env.get('value')}")
                    if secrets := container.get('secrets', []):
                        print_red("Secrets:")
                        for secret in secrets:
                            print(f"{secret.get('name')}: {secret.get('valueFrom')}")
        except Exception as e:
            if self.debug:
                print_red(f"Error in task definition handler: {str(e)}")

    def _handle_list_tasks(self, action, cluster):
        print_yellow(f"\n[*] Found {action} permission - Listing tasks for cluster {cluster}")
        try:
            tasks = self.list_tasks(cluster)
            if tasks:
                task_details = self.describe_tasks(cluster, tasks)
                for task in task_details:
                    print_yellow(f"\nTask: {task.get('taskArn').split('/')[-1]}")
                    task_data = [
                        ['Status', task.get('lastStatus')],
                        ['Task Definition', task.get('taskDefinitionArn').split('/')[-1]],
                        ['Started At', task.get('startedAt')],
                        ['Group', task.get('group')]
                    ]
                    print(tabulate(task_data, tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error in tasks handler: {str(e)}")

    def _handle_list_container_instances(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing container instances")
        try:
            if resource == '*':
                clusters = self.list_clusters()
                for cluster_arn in clusters:
                    cluster_name = cluster_arn.split('/')[-1]
                    self._display_container_instances(cluster_name)
            else:
                cluster_name = resource.split('/')[-1]
                self._display_container_instances(cluster_name)
        except Exception as e:
            if self.debug:
                print_red(f"Error in container instances handler: {str(e)}")

    def _display_container_instances(self, cluster_name):
        instances = self.list_container_instances(cluster_name)
        if instances:
            instance_details = self.describe_container_instances(cluster_name, instances)
            print_yellow(f"\nContainer Instances in cluster {cluster_name}:")
            for instance in instance_details:
                instance_data = [
                    ['Instance ID', instance.get('ec2InstanceId')],
                    ['Status', instance.get('status')],
                    ['Running Tasks', instance.get('runningTasksCount')],
                    ['Agent Connected', instance.get('agentConnected')],
                    ['Docker Version', instance.get('versionInfo', {}).get('dockerVersion')]
                ]
                print(tabulate(instance_data, tablefmt='simple'))

    def _handle_describe_task_sets(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Describing task sets")
        try:
            if resource == '*':
                clusters = self.list_clusters()
                for cluster_arn in clusters:
                    cluster_name = cluster_arn.split('/')[-1]
                    # Don't automatically call list_services
                    services = self.list_services(cluster_name)
                    for service_arn in services:
                        service_name = service_arn.split('/')[-1]
                        self._display_task_sets(cluster_name, service_name)
            else:
                cluster_name, service_name = resource.split('/')[-2:]
                self._display_task_sets(cluster_name, service_name)
        except Exception as e:
            if self.debug:
                print_red(f"Error in task sets handler: {str(e)}")

    def _display_task_sets(self, cluster_name, service_name):
        try:
            task_sets = self.describe_task_sets(cluster_name, service_name)
            if task_sets:
                print_yellow(f"\nTask Sets for service {service_name} in cluster {cluster_name}:")
                for task_set in task_sets:
                    task_set_data = [
                        ['ID', task_set.get('id')],
                        ['Status', task_set.get('status')],
                        ['Task Definition', task_set.get('taskDefinition')],
                        ['Scale', f"{task_set.get('scale', {}).get('value')}%"],
                        ['Stability Status', task_set.get('stabilityStatus')]
                    ]
                    print(tabulate(task_set_data, tablefmt='simple'))
        except Exception as e:
            if self.debug:
                print_red(f"Error displaying task sets: {str(e)}")

    def _handle_list_task_definition_families(self, action, resource):
        print_yellow(f"\n[*] Found {action} permission - Listing task definition families")
        try:
            families = self.list_task_definition_families()
            if families:
                print_yellow("\nTask Definition Families:")
                for family in families:
                    print(f"- {family}")
            else:
                print_yellow("No task definition families found.")
        except Exception as e:
            if self.debug:
                print_red(f"Error in task definition families handler: {str(e)}")

    # API wrapper methods
    def list_clusters(self):
        try:
            clusters = []
            paginator = self.client.get_paginator('list_clusters')
            for page in paginator.paginate():
                clusters.extend(page.get('clusterArns', []))
            return clusters
        except ClientError as e:
            if self.debug:
                print_red(f"Error listing clusters: {e.response['Error']['Message']}")
            return []

    def describe_clusters(self, clusters):
        response = self.client.describe_clusters(clusters=clusters)
        return response.get('clusters', [])

    def list_services(self, cluster):
        try:
            services = []
            paginator = self.client.get_paginator('list_services')
            for page in paginator.paginate(cluster=cluster):
                services.extend(page.get('serviceArns', []))
            return services
        except ClientError as e:
            if self.debug:
                print_red(f"Error listing services: {e.response['Error']['Message']}")
            return []

    def describe_services(self, cluster, services):
        response = self.client.describe_services(cluster=cluster, services=services)
        return response.get('services', [])

    def list_tasks(self, cluster):
        try:
            tasks = []
            paginator = self.client.get_paginator('list_tasks')
            for page in paginator.paginate(cluster=cluster):
                tasks.extend(page.get('taskArns', []))
            return tasks
        except ClientError as e:
            if self.debug:
                print_red(f"Error listing tasks: {e.response['Error']['Message']}")
            return []

    def describe_tasks(self, cluster, tasks):
        response = self.client.describe_tasks(cluster=cluster, tasks=tasks)
        return response.get('tasks', [])

    def list_task_definitions(self):
        try:
            task_defs = []
            paginator = self.client.get_paginator('list_task_definitions')
            for page in paginator.paginate():
                task_defs.extend(page.get('taskDefinitionArns', []))
            return task_defs
        except ClientError as e:
            if self.debug:
                print_red(f"Error listing task definitions: {e.response['Error']['Message']}")
            return []

    def describe_task_definition(self, task_definition):
        response = self.client.describe_task_definition(taskDefinition=task_definition)
        return response.get('taskDefinition')

    def list_container_instances(self, cluster):
        try:
            instances = []
            paginator = self.client.get_paginator('list_container_instances')
            for page in paginator.paginate(cluster=cluster):
                instances.extend(page.get('containerInstanceArns', []))
            return instances
        except ClientError as e:
            if self.debug:
                print_red(f"Error listing container instances: {e.response['Error']['Message']}")
            return []

    def describe_container_instances(self, cluster, instances):
        response = self.client.describe_container_instances(
            cluster=cluster,
            containerInstances=instances
        )
        return response.get('containerInstances', [])

    def describe_task_sets(self, cluster, service):
        response = self.client.describe_task_sets(
            cluster=cluster,
            service=service
        )
        return response.get('taskSets', [])

    def list_task_definition_families(self):
        try:
            families = []
            paginator = self.client.get_paginator('list_task_definition_families')
            for page in paginator.paginate():
                families.extend(page.get('families', []))
            return families
        except ClientError as e:
            if self.debug:
                print_red(f"Error listing task definition families: {e.response['Error']['Message']}")
            return families
