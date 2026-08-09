from dataclasses import dataclass


@dataclass
class FarmSituation:
    """
    Represents current farm operational situation.

    Future extensions:

    - live herd state
    - production variance
    - financial position
    - risk indicators
    """


    situation_id: str

    farm_id: str

    status: str

    priority: str
