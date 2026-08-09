from dataclasses import dataclass


@dataclass
class DailyOperatingBoard:

    farm_name: str

    operating_status: str

    critical_tasks: list

    risk_count: int

    pending_decisions: int
