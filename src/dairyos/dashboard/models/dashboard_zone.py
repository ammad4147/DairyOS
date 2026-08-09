from dataclasses import dataclass, field

from dairyos.dashboard.models.dashboard_widget import (
    DashboardWidget,
)


@dataclass
class DashboardZone:
    """
    Dashboard section.

    Contains widgets.
    """

    zone_id: str

    title: str

    widgets: list[DashboardWidget] = field(
        default_factory=list
    )

    visible: bool = True
