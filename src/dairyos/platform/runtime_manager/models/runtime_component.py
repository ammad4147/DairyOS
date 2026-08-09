from dataclasses import dataclass


@dataclass
class RuntimeComponent:
    """
    Represents a managed runtime component.
    """

    name: str

    enabled: bool = True
