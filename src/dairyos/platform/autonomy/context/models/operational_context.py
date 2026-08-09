from dataclasses import dataclass



@dataclass
class OperationalContext:

    department: str

    metrics: dict

    events: list

    risks: list

