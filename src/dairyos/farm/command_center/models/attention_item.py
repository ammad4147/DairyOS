from dataclasses import dataclass


@dataclass
class AttentionItem:
    """
    Represents an operational issue
    requiring attention.

    Composition model only.
    No business rules.
    """

    priority: str

    area: str

    message: str

    action_required: bool = True

    animal_id: str | None = None
