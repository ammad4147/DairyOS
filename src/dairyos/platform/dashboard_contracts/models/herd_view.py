from dataclasses import dataclass



@dataclass
class HerdSituation:

    total_animals: int

    milking_animals: int

    dry_animals: int

    health_alerts: int

