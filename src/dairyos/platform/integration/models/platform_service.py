from dataclasses import dataclass


@dataclass
class PlatformService:

    """
    Represents a service exposed to
    DairyOS enterprise runtime.
    """

    name: str

    service: object

    enabled: bool = True
