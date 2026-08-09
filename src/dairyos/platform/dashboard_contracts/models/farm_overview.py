from dataclasses import dataclass



@dataclass
class FarmOverview:

    farm_id: str

    status: str

    animal_count: int

    daily_milk: float

    alerts: int

