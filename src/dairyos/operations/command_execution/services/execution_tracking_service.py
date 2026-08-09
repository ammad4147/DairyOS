from ..models.execution_status import ExecutionStatus


class ExecutionTrackingService:
    """
    Updates command execution progress.
    """


    def start(
        self,
        execution,
    ):

        execution.status = ExecutionStatus.IN_PROGRESS

        return execution


    def complete(
        self,
        execution,
    ):

        execution.status = ExecutionStatus.COMPLETED

        return execution


    def failed(
        self,
        execution,
    ):

        execution.status = ExecutionStatus.FAILED

        return execution
