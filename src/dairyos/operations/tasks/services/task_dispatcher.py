from dairyos.operations.tasks.models.task_type import (
    TaskType,
)



class TaskDispatcher:
    """
    Executes operational tasks
    through registered handlers.
    """



    def __init__(
        self,
    ):

        self.handlers = {}



    def register(
        self,
        task_type,
        handler,
    ):

        self.handlers[
            task_type
        ] = handler



    def dispatch(
        self,
        task,
    ):

        handler = self.handlers.get(
            task.task_type
        )


        if handler is None:

            raise ValueError(
                f"No handler registered for {task.task_type}"
            )


        return handler.handle(
            task
        )
