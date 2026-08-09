from dataclasses import dataclass



@dataclass
class IntelligenceBrief:


    farm_name: str

    issue: str

    risk_level: str

    escalation: str

    recommendation: str

    confidence: int
