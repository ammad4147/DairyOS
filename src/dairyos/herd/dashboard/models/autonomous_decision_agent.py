from dataclasses import dataclass, field



@dataclass
class AutonomousDecisionAgent:


    condition: str

    recommended_action: str

    confidence: float

    priority: str

    workflow_steps: list = field(default_factory=list)
