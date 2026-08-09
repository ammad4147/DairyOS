from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardAlert:
    """
    Operational alert displayed to farm users.
    """

    title: str
    message: str
    severity: str
    source: str
