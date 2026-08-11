from enum import Enum


class OperationalInputType(str, Enum):
    """
    Canonical DairyOS operational input categories.
    """

    MILK_PRODUCTION = "milk_production"

    FEEDING = "feeding"

    ANIMAL_HEALTH = "animal_health"

    BREEDING = "breeding"

    WORKFORCE = "workforce"

    INVENTORY = "inventory"

    FINANCIAL = "financial"

    EQUIPMENT = "equipment"

    TREATMENT = "treatment"
