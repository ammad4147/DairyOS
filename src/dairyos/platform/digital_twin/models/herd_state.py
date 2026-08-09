from dataclasses import dataclass



@dataclass
class HerdState:

    total_animals: int

    milking_cows: int

    dry_cows: int

    heifers: int

    calves: int

    replacement_rate: float

