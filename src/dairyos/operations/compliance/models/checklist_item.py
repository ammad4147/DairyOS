from dataclasses import dataclass


@dataclass
class ChecklistItem:
    """
    Defines a checklist requirement.
    """

    item_id: str
    description: str
    mandatory: bool
