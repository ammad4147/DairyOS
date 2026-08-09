from enum import Enum


class UserRole(str, Enum):
    """
    Operational farm user roles.
    """

    OWNER = "owner"
    FARM_MANAGER = "farm_manager"
    VETERINARIAN = "veterinarian"
    ACCOUNTANT = "accountant"
    STORE_KEEPER = "store_keeper"
    MILKING_OPERATOR = "milking_operator"
    FEED_SUPERVISOR = "feed_supervisor"
    AI_TECHNICIAN = "ai_technician"
    LABOURER = "labourer"
