from dataclasses import dataclass


@dataclass
class MilkCommand:
    """
    Dashboard command view for milk operations.

    Read model only.
    Does not own milk domain logic.
    """

    today_litres: float = 0.0

    yesterday_litres: float = 0.0

    week_litres: float = 0.0

    month_litres: float = 0.0

    milking_animals: int = 0

    average_litres_per_animal: float = 0.0

    production_status: str = "UNKNOWN"

    target_variance_litres: float = 0.0
