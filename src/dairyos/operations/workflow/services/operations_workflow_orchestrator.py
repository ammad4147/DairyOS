from typing import List

from ..models.operational_workflow_event import OperationalWorkflowEvent
from ..models.operational_workflow_result import OperationalWorkflowResult


class OperationsWorkflowOrchestrator:
    """
    Coordinates the operational lifecycle:

    Signal
       |
       v
    Decision
       |
       v
    Action
       |
       v
    Outcome
    """

    def __init__(self):
        self.events: List[OperationalWorkflowEvent] = []


    def submit_event(
        self,
        event: OperationalWorkflowEvent,
    ) -> OperationalWorkflowEvent:

        self.events.append(event)

        return event


    def process_event(
        self,
        event: OperationalWorkflowEvent,
    ) -> OperationalWorkflowResult:

        return OperationalWorkflowResult(
            event_id=event.event_id,
            decision_created=True,
            action_created=True,
            outcome_tracking_enabled=True,
            workflow_status="ACTIVE",
        )


    def process_all(self) -> List[OperationalWorkflowResult]:

        return [
            self.process_event(event)
            for event in self.events
        ]
