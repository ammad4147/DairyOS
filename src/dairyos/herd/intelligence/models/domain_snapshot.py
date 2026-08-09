from dataclasses import dataclass



@dataclass
class DomainSnapshot:


    health_events: int = 0

    vaccinations: int = 0

    milk_records: int = 0

    production_groups: int = 0

    feed_plans: int = 0

    consumptions: int = 0

    pregnancies: int = 0

    costs: int = 0

    revenues: int = 0
