from dataclasses import dataclass


@dataclass
class ExecutiveSummary:

    farm_name: str

    health_score: float

    operational_status: str

    active_priorities: int

    pending_decisions: int

    critical_issues: int

