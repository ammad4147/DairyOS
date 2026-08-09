from enum import Enum


class NotificationType(Enum):
    """
    Operational notification categories.
    """

    ALERT = "ALERT"
    REMINDER = "REMINDER"
    ESCALATION = "ESCALATION"
    INFORMATION = "INFORMATION"
