from dataclasses import dataclass



@dataclass
class ExecutiveReport:


    farm_name: str

    farm_status: str

    health_score: int

    production_score: int

    reproduction_score: int

    financial_score: int

    pending_actions: int

    management_effectiveness: int

    priority_message: str
