from dataclasses import dataclass


@dataclass
class ExecutiveCommandCenter:

    farm_name: str

    overall_score: int

    risk_level: str

    decision_required: bool

    priority_level: str

    top_decision: str

    recommended_action: str

    business_impact: str

    time_horizon: str
