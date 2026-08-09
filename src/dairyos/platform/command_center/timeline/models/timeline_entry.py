from dataclasses import dataclass



@dataclass
class TimelineEntry:

    timestamp: str

    title: str

    source: str

    details: dict

