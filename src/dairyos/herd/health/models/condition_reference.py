from dataclasses import dataclass


@dataclass
class ConditionReference:

    condition_name: str

    category: str

    related_indicators: list

    recommended_checks: list

    source: str
