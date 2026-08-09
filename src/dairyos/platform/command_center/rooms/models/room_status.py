from enum import Enum



class RoomStatus(str, Enum):

    HEALTHY = "healthy"

    WARNING = "warning"

    CRITICAL = "critical"

    UNKNOWN = "unknown"

