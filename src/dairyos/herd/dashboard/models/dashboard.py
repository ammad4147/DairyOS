from dataclasses import dataclass
from typing import Any, Dict, Optional


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

    data: Optional[Dict[str, Any]] = None


@dataclass
class DashboardView:
    """
    Dashboard presentation view model.
    """

    name: str

    payload: Optional[Dict[str, Any]] = None
