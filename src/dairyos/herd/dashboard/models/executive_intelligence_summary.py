from dataclasses import dataclass



@dataclass
class ExecutiveIntelligenceSummary:


    farm_status: str

    top_concern: str

    recommended_focus: str

    priority_actions: list

    owner_attention: bool
