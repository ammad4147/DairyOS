from enum import Enum


class DashboardActionStatus(str, Enum):
    """
    Operational lifecycle state
    of dashboard actions.
    """


    PENDING = "pending"

    IN_PROGRESS = "in_progress"

    COMPLETED = "completed"

    OVERDUE = "overdue"

    WARNING = "warning"

    CANCELLED = "cancelled"
