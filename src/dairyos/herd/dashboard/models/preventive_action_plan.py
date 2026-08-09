from dataclasses import dataclass



@dataclass
class PreventiveActionPlan:


    category: str

    risk_level: str

    priority: str

    actions: list

    timeline: str

    owner_attention: bool
