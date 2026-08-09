from enum import Enum



class AlertCategory(str, Enum):

    ANIMAL_HEALTH = "animal_health"

    MILK_PRODUCTION = "milk_production"

    FEED = "feed"

    REPRODUCTION = "reproduction"

    FINANCE = "finance"

    WORKFORCE = "workforce"

    SYSTEM = "system"

