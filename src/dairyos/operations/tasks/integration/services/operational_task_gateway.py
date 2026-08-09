from dairyos.operations.tasks.integration.models.task_execution_result import (
    TaskExecutionResult,
)



class OperationalTaskGateway:
    """
    Application boundary for operational task execution.
    """



    def __init__(
        self,
        dispatcher,
    ):

        self.dispatcher = dispatcher



    def execute(
        self,
        task,
    ):

        result = self.dispatcher.dispatch(
            task
        )


        return TaskExecutionResult(

            task_id=task.task_id,

            task_type=task.task_type,

            success=True,

            result=result,

        )
