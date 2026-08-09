from enum import Enum


class EventType(str, Enum):
    """
    Standard DairyOS operational event categories.
    """

    ANIMAL = "animal"
    PRODUCTION = "production"
    FEED = "feed"
    HEALTH = "health"
    REPRODUCTION = "reproduction"
    INVENTORY = "inventory"
    WORKFORCE = "workforce"
    EQUIPMENT = "equipment"
    SYSTEM = "system"
