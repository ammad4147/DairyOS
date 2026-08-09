from enum import Enum


class OperationalEventType(Enum):
    """
    Supported operational events.
    """

    TASK_CREATED = "TASK_CREATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_DELAYED = "TASK_DELAYED"
    HEALTH_ALERT = "HEALTH_ALERT"
    PRODUCTION_UPDATE = "PRODUCTION_UPDATE"
