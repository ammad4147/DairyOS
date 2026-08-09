from dataclasses import dataclass



@dataclass
class FarmSituation:
    """
    Daily operational condition snapshot.

    Represents what management needs
    to know before making decisions.
    """


    total_animals: int

    milking_cows: int

    dry_cows: int

    close_up_cows: int

    animals_requiring_attention: int

    daily_milk_litres: float

    milk_change_percentage: float

    feed_cost_per_litre: float

    reproduction_alerts: int

    overall_status: str
