from dataclasses import dataclass



@dataclass
class CommandCenterDashboard:


    farm_name: str

    farm_status: str

    health_score: int

    production_score: int

    reproduction_score: int

    financial_score: int

    pending_actions: int

    recommendations_count: int

    historical_actions: int

    effectiveness_score: int

    priority_message: str
