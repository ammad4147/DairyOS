from enum import Enum



class NavigationLevel(str, Enum):

    EXECUTIVE = "executive"

    FARM = "farm"

    DOMAIN = "domain"

    ENTITY = "entity"

    EVENT = "event"

