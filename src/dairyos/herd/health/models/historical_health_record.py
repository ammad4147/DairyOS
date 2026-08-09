from dataclasses import dataclass
from datetime import date


@dataclass
class HistoricalHealthRecord:

    animal_id: str

    condition: str

    event_date: date

    treatment: str

    outcome: str

    source: str

    verified: bool
