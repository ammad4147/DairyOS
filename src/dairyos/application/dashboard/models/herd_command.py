from dataclasses import dataclass


@dataclass
class HerdCommand:
    """
    Dashboard command view for herd operations.

    Read model only.
    """

    total_animals: int = 0

    milking_animals: int = 0

    dry_animals: int = 0

    calves: int = 0

    heifers: int = 0

    animals_attention_required: int = 0

    lifecycle_summary: dict = None

    def __post_init__(self):
        if self.lifecycle_summary is None:
            self.lifecycle_summary = {}
