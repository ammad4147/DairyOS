from dataclasses import dataclass


@dataclass
class FarmCommandCenter:

    farm_name: str

    operational_status: str

    risk_level: str

    executive_score: int

    priorities: list

    owner_actions: list

    active_alerts: int
