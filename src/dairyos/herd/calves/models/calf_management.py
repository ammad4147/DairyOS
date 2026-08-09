from dataclasses import dataclass



@dataclass
class CalfManagement:


    animal_id: str

    age_months: int

    sex: str

    growth_stage: str

    priority: str

    action: str
