from dairyos.operations.accountability_integration.services.accountability_bridge import (
    AccountabilityBridge,
)


class ExecutionAccountabilityBridge:
    """
    Connects operational execution
    with staff accountability tracking.

    Flow:

    OperationalExecution
            |
            v
    ExecutionAccountability

    Does not:
    - complete execution
    - verify execution
    - alter operational facts
    """


    def __init__(
        self,
        accountability_bridge: AccountabilityBridge | None = None,
    ):

        self.accountability_bridge = (
            accountability_bridge
            if accountability_bridge is not None
            else AccountabilityBridge()
        )


    def register_execution(
        self,
        execution,
        task_name: str,
    ):

        return (
            self.accountability_bridge
            .create_accountability_record(
                execution,
                task_name,
            )
        )


    def get_records(self):

        return (
            self.accountability_bridge
            .get_records()
        )
