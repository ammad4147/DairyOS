from enum import Enum


class TaskType(str, Enum):

    MILKING = "milking"

    FEEDING = "feeding"

    HEALTH_CHECK = "health_check"

    AI_SERVICE = "artificial_insemination"

    CLEANING = "cleaning"

    INVENTORY = "inventory"

    MAINTENANCE = "maintenance"
