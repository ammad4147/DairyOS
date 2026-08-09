from dataclasses import dataclass, field

from dairyos.dashboard.models.dashboard_zone import (
    DashboardZone,
)


@dataclass
class DashboardLayout:
    """
    Dashboard layout.

    Presentation only.
    """

    zones: list[DashboardZone] = field(
        default_factory=list
    )
