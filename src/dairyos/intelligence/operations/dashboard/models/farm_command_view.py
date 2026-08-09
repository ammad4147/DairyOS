from dataclasses import dataclass


@dataclass
class FarmCommandView:
    """
    Owner-facing dairy farm command summary.

    Converts operational intelligence
    into human decision information.
    """


    total_animals: int

    milking_cows: int

    dry_cows: int

    close_up_cows: int


    daily_milk_litres: float

    previous_day_milk_litres: float


    milk_change_percentage: float


    feed_cost_per_litre: float


    animals_requiring_attention: int


    reproduction_alerts: int


    active_tasks: int


    overall_status: str
