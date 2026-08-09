from dataclasses import dataclass


@dataclass
class ComplianceCheck:
    """
    Records procedure compliance status.
    """

    check_id: str
    procedure_id: str
    status: str
    completion_percentage: float
