from dataclasses import dataclass


@dataclass
class MilkQualityRecord:

    record_id: str

    temperature: float | None = None

    quality_notes: str = ""
