from dataclasses import dataclass



@dataclass
class CullingDecision:


    animal_id: str

    production_status: str

    health_status: str

    replacement_available: bool

    recommendation: str

    action: str
