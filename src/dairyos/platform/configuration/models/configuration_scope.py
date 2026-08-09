from enum import Enum



class ConfigurationScope(str, Enum):

    GLOBAL = "global"

    TENANT = "tenant"

    FARM = "farm"

    USER = "user"
