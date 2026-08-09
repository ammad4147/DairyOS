from enum import Enum



class TaskStatus(str, Enum):

    CREATED = "created"

    ASSIGNED = "assigned"

    IN_PROGRESS = "in_progress"

    COMPLETED = "completed"

    CANCELLED = "cancelled"

