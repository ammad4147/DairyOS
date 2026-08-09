from dataclasses import dataclass
from typing import Any


@dataclass
class OperationalInputCommand:
    """
    Command representing a farm operational input.
    """

    input_type: str

    payload: dict[str, Any]

    source: str

    actor: str

