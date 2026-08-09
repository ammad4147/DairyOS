from dataclasses import dataclass


@dataclass
class OperationalWorkflowResult:
    """
    Result produced after workflow processing.
    """

    event_id: str
    decision_created: bool
    action_created: bool
    outcome_tracking_enabled: bool
    workflow_status: str
