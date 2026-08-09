from dataclasses import dataclass



@dataclass
class AccessResult:

    allowed: bool

    reason: str

