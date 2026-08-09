from dataclasses import dataclass



@dataclass
class OperationalState:

    feed_cost_daily: float

    labour_status: str

    operational_score: float

    active_alerts: int

