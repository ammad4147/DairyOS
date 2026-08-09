from dataclasses import dataclass


@dataclass
class DashboardWidget:
    """
    Reusable dashboard widget.

    Presentation model only.
    """

    widget_id: str

    title: str

    subtitle: str = ""

    value: object | None = None

    status: str = ""

    trend: str = ""

    zone: str = ""

    position: int = 0

    size: str = "MEDIUM"

    visible: bool = True

    user_configurable: bool = True

    refresh_interval_seconds: int = 60

    importance: str = "NORMAL"

    actionability: str = "INFORMATION"

    last_updated: str | None = None

    data_freshness: str = "CURRENT"

    has_alert: bool = False

    has_action: bool = False

    click_target: str | None = None
