from enum import Enum


class DashboardSection(str, Enum):
    """
    Operational dashboard visibility sections.

    Sections represent information areas
    available to farm users.
    """

    HERD = "herd"

    PRODUCTION = "production"

    FINANCE = "finance"

    FEED = "feed"

    HEALTH = "health"

    MILKING = "milking"

    TASKS = "tasks"

    ALERTS = "alerts"

    OPERATIONS = "operations"
