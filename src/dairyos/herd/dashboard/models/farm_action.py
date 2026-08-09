from dataclasses import dataclass


@dataclass
class FarmAction:

    title: str

    category: str

    priority: str

    status: str

    assigned_to: str

    timeframe: str

    completed: bool = False
