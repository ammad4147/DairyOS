from dataclasses import dataclass, field


@dataclass
class FeedingDay:

    day_id: str
    date: str
    records: list = field(default_factory=list)
    closed: bool = False
