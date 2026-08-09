from dataclasses import dataclass



@dataclass
class PlatformPolicy:

    """
    Enterprise runtime policy definition.
    """

    name: str

    enabled: bool = True

    description: str = ""
