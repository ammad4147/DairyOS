from dataclasses import dataclass, field

from dairyos.application.dashboard.policies.dashboard_section import (
    DashboardSection,
)


@dataclass(frozen=True)
class DashboardRoleProfile:
    """
    Defines the dashboard experience
    assigned to an operational farm role.

    Read configuration model only.

    Does not contain business calculations.
    """

    role_name: str

    sections: set[DashboardSection] = field(
        default_factory=set
    )

    priority_metrics: list[str] = field(
        default_factory=list
    )
