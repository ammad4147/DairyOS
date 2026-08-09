from dairyos.platform.workflow.models.workflow_definition import WorkflowDefinition
from dairyos.platform.workflow.models.workflow_instance import WorkflowInstance
from dairyos.platform.workflow.models.workflow_status import WorkflowStatus


class WorkflowService:

    def __init__(self):

        self.definitions = []
        self.instances = []


    def register(self, workflow: WorkflowDefinition):

        self.definitions.append(workflow)

        return workflow


    def start(self, workflow: WorkflowDefinition):

        instance = WorkflowInstance(
            workflow=workflow,
            status=WorkflowStatus.RUNNING
        )

        if workflow.steps:
            instance.current_step = workflow.steps[0]

        self.instances.append(instance)

        return instance


    def complete(self, instance: WorkflowInstance, result: str = ""):

        instance.status = WorkflowStatus.COMPLETED
        instance.result = result

        return instance


    def fail(self, instance: WorkflowInstance, reason: str = ""):

        instance.status = WorkflowStatus.FAILED
        instance.result = reason

        return instance


    def history(self):

        return self.instances
