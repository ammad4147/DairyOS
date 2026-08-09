from dataclasses import dataclass, field

from dairyos.dashboard.models.dashboard_layout import (
    DashboardLayout,
)


@dataclass
class DashboardView:
    """
    Root dashboard model.

    Owner-facing presentation.
    """

    layout: DashboardLayout

    owner_attention: list = field(
        default_factory=list
    )

    farm_timeline: list = field(
        default_factory=list
    )

    quick_actions: list = field(
        default_factory=list
    )

    animal_spotlight: list = field(
        default_factory=list
    )
