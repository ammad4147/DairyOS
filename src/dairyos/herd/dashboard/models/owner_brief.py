from dataclasses import dataclass



@dataclass
class OwnerBrief:


    farm_name: str

    status: str

    primary_issue: str

    risk_level: str

    recommendation: str

    owner_action: str

    confidence: int
