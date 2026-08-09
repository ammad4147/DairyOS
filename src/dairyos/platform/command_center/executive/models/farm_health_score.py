from dataclasses import dataclass


@dataclass
class FarmHealthScore:

    score: float

    status: str

    factors: dict

