from enum import Enum



class AuditEventType(str, Enum):

    USER_ACTION = "user_action"

    SYSTEM_EVENT = "system_event"

    SECURITY_EVENT = "security_event"

    WORKFLOW_EVENT = "workflow_event"

    DECISION_EVENT = "decision_event"

