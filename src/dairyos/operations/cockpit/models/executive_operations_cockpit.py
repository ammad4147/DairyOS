from dataclasses import dataclass


@dataclass
class ExecutiveOperationsCockpit:
    """
    Executive operational command view.
    """

    overall_status: str
    risk_level: str
    management_focus: str
    action_required: bool
    operational_score: float
