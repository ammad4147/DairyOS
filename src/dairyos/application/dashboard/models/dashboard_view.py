from dataclasses import dataclass, field

from .farm_today import FarmTodaySnapshot
from ..policies.dashboard_section import DashboardSection


@dataclass
class DashboardView:
    """
    User-specific dashboard presentation model.

    Wraps operational dashboard data
    with visibility information.

    Does not modify domain data.
    """

    snapshot: FarmTodaySnapshot

    visible_sections: set[DashboardSection] = field(
        default_factory=set
    )
