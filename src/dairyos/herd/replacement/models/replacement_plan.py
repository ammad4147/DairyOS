from dataclasses import dataclass



@dataclass
class ReplacementPlan:


    current_lactating_cows: int

    culling_rate: float

    required_replacements: int

    available_heifers: int

    status: str

    action: str
