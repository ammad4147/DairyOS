from dataclasses import dataclass



@dataclass
class SafetyCheck:

    allowed: bool

    reason: str

