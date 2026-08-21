from dataclasses import dataclass
from datetime import datetime, UTC



@dataclass
class MilkQualityRecord:
    """
    Represents a milk quality testing entry.

    Tracks fat percentage, SNF (Solids-Not-Fat), density,
    and bacterial count for quality premiums and compliance.
    """


    record_id: str

    animal_id: str

    milking_session: str

    litres: float

    fat_pct: float

    snf_pct: float

    density: float

    bacterial_count: int

    recorded_by: str

    recorded_at: datetime = datetime.now(UTC)
