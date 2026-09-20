from dataclasses import dataclass
from typing import Any


@dataclass
class HerdDashboard:
    """
    Herd operational dashboard summary.
    """

    farm_name: str

    total_animals: int

    milking_cows: int

    dry_cows: int

    heifers: int

    calves: int

    capacity: int


@dataclass
class Dashboard:
    """
    Generic dashboard container used by rendering and services.
    """

    title: str = "DairyOS Dashboard"

    data: dict[str, Any] | None = None


@dataclass
class DashboardView:
    """
    Dashboard presentation view model.
    """

    name: str

    payload: dict[str, Any] | None = None
