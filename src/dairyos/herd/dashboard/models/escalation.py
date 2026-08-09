from dataclasses import dataclass



@dataclass
class Escalation:

    level: str

    response_owner: str

    response_time: str

    reason: str

    priority_score: int
