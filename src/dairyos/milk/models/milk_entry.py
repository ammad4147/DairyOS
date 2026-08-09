from dataclasses import dataclass, field
from datetime import datetime, timezone

from dairyos.milk.models.milking_session import MilkingSession


@dataclass
class MilkEntry:

    entry_id: str

    animal_id: str

    session: MilkingSession

    litres: float

    operator: str

    entry_time: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def validate(self):

        if not self.animal_id:
            raise ValueError(
                "Animal ID required"
            )

        if self.litres < 0:
            raise ValueError(
                "Milk quantity cannot be negative"
            )

        if not self.operator:
            raise ValueError(
                "Operator required"
            )

        return True
