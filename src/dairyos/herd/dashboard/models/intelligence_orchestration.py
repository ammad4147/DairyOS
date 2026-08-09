from dataclasses import dataclass



@dataclass
class IntelligenceOrchestration:


    overall_status: str

    primary_issue: str

    recommended_action: str

    confidence: int

    priority: str
