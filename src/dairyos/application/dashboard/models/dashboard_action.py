from dataclasses import dataclass

from .dashboard_action_status import DashboardActionStatus


@dataclass(frozen=True)
class DashboardAction:
    """
    Operational dashboard action.

    Represents a recommended next step
    for a farm user.

    Supports:
    - generated operational actions
    - role responsibility actions

    Dashboard actions do not execute
    domain operations.
    """

    title: str

    description: str = ""

    status: DashboardActionStatus = (
        DashboardActionStatus.PENDING
    )

    source: str = "dashboard"

    action_type: str = ""

    priority: str = "normal"

    responsible_role: str = ""
