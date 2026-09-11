from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite

from dairyos.milk.models.milking_session import MilkingSession


@dataclass
class MilkRecord:
    """
    Permanent production record created from verified milking activity.

    Represents measured milk output from an individual animal.
    """

    record_id: str

    animal_id: str

    session: MilkingSession

    quantity_litres: float

    operator: str

    recorded_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def validate(self):

        if not self.animal_id:
            raise ValueError(
                "Animal ID required"
            )

        quantity_litres = float(self.quantity_litres)
        if not isfinite(quantity_litres) or quantity_litres < 0:
            raise ValueError(
                "Milk quantity must be finite and cannot be negative"
            )

        if not self.operator:
            raise ValueError(
                "Operator required"
            )

        return True
