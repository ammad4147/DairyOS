from dataclasses import dataclass



@dataclass
class ActionPlan:

    title: str

    description: str

    assigned_to: str

    priority: str

    status: str = "draft"

