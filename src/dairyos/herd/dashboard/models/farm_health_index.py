from dataclasses import dataclass


@dataclass
class FarmHealthIndex:

    production_score: int

    health_score: int

    reproduction_score: int

    financial_score: int

    overall_score: int
