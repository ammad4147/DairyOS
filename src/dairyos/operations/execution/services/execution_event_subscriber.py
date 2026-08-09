from dairyos.operations.execution.services.execution_lifecycle_event_handler import (
    ExecutionLifecycleEventHandler,
)


class ExecutionEventSubscriber:
    """
    Receives FarmOperationEvents related to
    execution lifecycle and forwards them
    to execution lifecycle handling.
    """


    EXECUTION_EVENTS = {

        "OPERATIONAL_EXECUTION_COMPLETED",

        "OPERATIONAL_EXECUTION_VERIFIED",

    }


    def __init__(
        self,
        handler=None,
        execution_service=None,
    ):

        if handler is not None:

            self.handler = handler

        elif execution_service is not None:

            self.handler = ExecutionLifecycleEventHandler(
                execution_service=execution_service
            )

        else:

            raise ValueError(
                "ExecutionEventSubscriber requires execution lifecycle handler"
            )


    def handle(
        self,
        event,
    ):

        if event.event_type not in self.EXECUTION_EVENTS:

            return None


        return self.handler.handle(
            event
        )
