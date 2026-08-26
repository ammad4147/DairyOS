from enum import Enum


class OperationalInputType(str, Enum):
    """
    Canonical DairyOS operational input categories.
    """

    MILK_PRODUCTION = "milk_production"

    MILKING_SESSION_NOT_MILKED = "milking_session_not_milked"

    FEEDING = "feeding"

    FEED_RATION = "feed_ration"

    ANIMAL_HEALTH = "animal_health"

    BREEDING = "breeding"

    ANIMAL_LIFECYCLE = "animal_lifecycle"

    ANIMAL_DISPOSITION = "animal_disposition"

    ANIMAL_PROFILE_UPDATE = "animal_profile_update"

    YOUNGSTOCK_GROWTH = "youngstock_growth"

    YOUNGSTOCK_WEANING = "youngstock_weaning"

    WORKFORCE = "workforce"

    INVENTORY = "inventory"

    FINANCIAL = "financial"

    EQUIPMENT = "equipment"

    TREATMENT = "treatment"
