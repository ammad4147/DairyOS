from enum import Enum



class CommandPermission(str, Enum):

    VIEW = "view"

    ACKNOWLEDGE = "acknowledge"

    EXECUTE = "execute"

    OVERRIDE = "override"

    ADMIN = "admin"

