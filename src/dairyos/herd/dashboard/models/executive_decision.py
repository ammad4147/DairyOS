from dataclasses import dataclass


@dataclass
class ExecutiveDecision:

    farm_name: str

    decision_required: bool

    priority_level: str

    risk_level: str

    recommended_action: str

    business_impact: str

    time_horizon: str
