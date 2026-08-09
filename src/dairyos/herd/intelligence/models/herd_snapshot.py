from dataclasses import dataclass


@dataclass
class HerdSnapshot:

    total_animals: int

    milking_cows: int

    dry_cows: int

    heifers: int

    calves: int
