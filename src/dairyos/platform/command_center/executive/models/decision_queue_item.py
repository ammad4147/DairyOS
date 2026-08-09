from dataclasses import dataclass


@dataclass
class DecisionQueueItem:

    title: str

    priority: str

    source: str

    recommended_action: str

