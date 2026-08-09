from enum import Enum



class TimelineEventType(str, Enum):

    OPERATION = "operation"

    ALERT = "alert"

    DECISION = "decision"

    WORKFLOW = "workflow"

    SYSTEM = "system"

