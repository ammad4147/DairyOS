from dataclasses import dataclass


@dataclass
class Ownership:
    domain: str
    owner: str
    team: str
