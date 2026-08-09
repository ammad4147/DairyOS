from dataclasses import dataclass
from datetime import datetime


@dataclass
class DecisionContext:
    """
    Context information used to generate decisions.
    """

    source: str
    category: str
    description: str
    operational_impact: str

