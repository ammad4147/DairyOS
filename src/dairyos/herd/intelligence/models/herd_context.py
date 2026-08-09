from dataclasses import dataclass



@dataclass
class HerdContext:


    farm_name: str

    total_animals: int

    health_alerts: int = 0

    open_cows: int = 0

    replacement_shortage: bool = False

    production_status: str = "STABLE"

    financial_status: str = "POSITIVE"

    feed_status: str = "NORMAL"
