from dairyos.operations.tasks.handlers.task_handler import (
    TaskHandler,
)


from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class MilkingTaskHandler(TaskHandler):
    """
    Converts milking tasks into operational events.
    """

    def __init__(
        self,
        event_publisher,
    ):

        self.event_publisher = event_publisher



    def handle(
        self,
        task,
    ):

        event = OperationalEvent(

            event_type="production",

            entity_type="cow",

            entity_id=task.entity_id,

            actor=task.assigned_to,

            payload={

                "activity": "milking",

                "task_id": task.task_id,

            },

        )


        return self.event_publisher.publish(
            event
        )
