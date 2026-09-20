from dataclasses import dataclass


@dataclass
class OperationalPattern:
    """
    Represents repeated operational behaviour.
    """

    pattern_id: str
    name: str
    category: str
    occurrence_count: int
    impact_level: str
    signal_ids: list[str]
