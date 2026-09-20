from dataclasses import dataclass


@dataclass
class DecisionContext:
    """
    Context information used to generate decisions.
    """

    source: str
    category: str
    description: str
    operational_impact: str

