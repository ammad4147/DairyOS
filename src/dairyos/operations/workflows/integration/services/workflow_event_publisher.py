from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class WorkflowEventPublisher:
    """
    Converts workflow lifecycle changes
    into operational events.
    """


    def __init__(
        self,
        event_publisher,
    ):

        self.event_publisher = event_publisher



    def publish_created(
        self,
        workflow,
    ):

        event = OperationalEvent(

            event_type="workflow_created",

            entity_type="workflow",

            entity_id=workflow.workflow_id,

            actor=workflow.assigned_to,

            payload={

                "task_id": workflow.task_id,

                "workflow_type": workflow.workflow_type,

                "status": workflow.status,

            },

        )


        return self.event_publisher.publish(
            event
        )



    def publish_started(
        self,
        workflow,
    ):

        event = OperationalEvent(

            event_type="workflow_started",

            entity_type="workflow",

            entity_id=workflow.workflow_id,

            actor=workflow.assigned_to,

            payload={

                "task_id": workflow.task_id,

                "workflow_type": workflow.workflow_type,

                "status": workflow.status,

            },

        )


        return self.event_publisher.publish(
            event
        )



    def publish_completed(
        self,
        workflow,
    ):

        event = OperationalEvent(

            event_type="workflow_completed",

            entity_type="workflow",

            entity_id=workflow.workflow_id,

            actor=workflow.assigned_to,

            payload={

                "task_id": workflow.task_id,

                "workflow_type": workflow.workflow_type,

                "status": workflow.status,

            },

        )


        return self.event_publisher.publish(
            event
        )
