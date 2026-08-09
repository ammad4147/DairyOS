from dairyos.operations.tasks.models.task_type import (
    TaskType,
)


from dairyos.operations.tasks.handlers.milking_task_handler import (
    MilkingTaskHandler,
)



class TaskRegistry:
    """
    Registers default operational task handlers.
    """



    def __init__(
        self,
        dispatcher,
        event_publisher,
    ):

        self.dispatcher = dispatcher

        self.event_publisher = event_publisher



    def register_defaults(
        self,
    ):

        milking_handler = MilkingTaskHandler(

            self.event_publisher

        )


        self.dispatcher.register(

            TaskType.MILKING.value,

            milking_handler,

        )


        return self.dispatcher
