from enum import Enum



class AutonomyPermission(str, Enum):

    OBSERVE = "observe"

    ASSIST = "assist"

    RECOMMEND = "recommend"

    APPROVE = "approve"

    EXECUTE = "execute"

