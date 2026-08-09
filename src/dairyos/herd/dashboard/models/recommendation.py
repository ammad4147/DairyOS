from dataclasses import dataclass


@dataclass
class Recommendation:

    category: str

    issue: str

    recommendation: str

    priority: str

    timeframe: str
