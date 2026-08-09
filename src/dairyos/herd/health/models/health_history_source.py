from dataclasses import dataclass


@dataclass
class HealthHistorySource:

    source_type: str

    source_name: str

    verified: bool

    confidence_level: str
