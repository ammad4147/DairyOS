from dataclasses import dataclass
from datetime import datetime, UTC



@dataclass
class InseminationRecord:
    """
    Represents artificial insemination.
    """


    insemination_id: str

    animal_id: str

    semen_type: str

    bull_reference: str

    technician: str

    inseminated_at: datetime = (
        datetime.now(UTC)
    )
