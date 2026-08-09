from dataclasses import dataclass



@dataclass
class AnimalInventory:


    animal_id: str

    breed: str

    age_months: int

    category: str

    lifecycle_status: str

    asset_status: str
