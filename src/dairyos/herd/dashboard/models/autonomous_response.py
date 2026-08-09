from dataclasses import dataclass, field



@dataclass
class AutonomousResponse:


    condition: str

    primary_response: str

    confidence: int

    supporting_actions: list = field(default_factory=list)
