from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from dairyos.operations.execution.services.execution_lifecycle_bridge import (
    ExecutionLifecycleBridge,
)


class ExecutionLifecycleEventHandler:
    """
    Consumes operational execution events
    and connects them to lifecycle consequences.

    Responsibilities:

    OperationalEvent
            |
            v
    Resolve execution
            |
            v
    ExecutionLifecycleBridge

    Does not:
    - change execution lifecycle
    - publish events
    - own execution rules
    """


    def __init__(
        self,
        execution_service: OperationalExecutionService,
        lifecycle_bridge: ExecutionLifecycleBridge | None = None,
    ):

        if execution_service is None:

            raise ValueError(
                "ExecutionLifecycleEventHandler requires OperationalExecutionService"
            )


        self.execution_service = execution_service


        self.lifecycle_bridge = (
            lifecycle_bridge
            if lifecycle_bridge is not None
            else ExecutionLifecycleBridge()
        )


    def handle(
        self,
        operational_event,
    ):

        event_type = operational_event.event_type


        if event_type not in [
            "OPERATIONAL_EXECUTION_COMPLETED",
            "OPERATIONAL_EXECUTION_VERIFIED",
        ]:

            return None


        execution_id = operational_event.entity_id


        execution = (
            self.execution_service.get_execution(
                execution_id
            )
        )


        if execution is None:

            raise ValueError(
                f"Execution not found: {execution_id}"
            )


        if event_type == "OPERATIONAL_EXECUTION_COMPLETED":

            return (
                self.lifecycle_bridge.record_execution_outcome(
                    execution=execution,
                    impact_score=0,
                    notes=execution.notes or "",
                )
            )


        if event_type == "OPERATIONAL_EXECUTION_VERIFIED":

            return (
                self.lifecycle_bridge.verify_execution(
                    execution=execution,
                    success=True,
                    message="Execution verified",
                )
            )
