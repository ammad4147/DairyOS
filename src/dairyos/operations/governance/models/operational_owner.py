from dataclasses import dataclass


@dataclass
class OperationalOwner:
    """
    Defines operational accountability.
    """

    owner_id: str
    name: str
    role: str
