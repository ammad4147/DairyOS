from dataclasses import dataclass


@dataclass
class FarmHealthReport:
    """
    Daily dairy farm health intelligence summary.

    Represents management understanding
    of current operational condition.
    """


    overall_status: str

    risk_level: str

    primary_concern: str

    contributing_factors: list[str]

    recommended_actions: list[str]
