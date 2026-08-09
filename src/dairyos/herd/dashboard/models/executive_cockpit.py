from dataclasses import dataclass, field



@dataclass
class ExecutiveCockpit:


    farm_name: str

    overall_score: int

    health_score: int

    production_score: int

    reproduction_score: int

    financial_score: int

    risk_level: str

    priority: str

    summary: str

    actions: list = field(default_factory=list)

    alerts: list = field(default_factory=list)
