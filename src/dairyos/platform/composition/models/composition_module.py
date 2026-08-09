from dataclasses import dataclass


@dataclass
class CompositionModule:

    """
    Represents a platform module participating
    in runtime composition.
    """

    name: str

    enabled: bool = True
