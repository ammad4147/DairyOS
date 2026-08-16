from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict


@dataclass
class MilkTraceabilityBatch:
    batch_id: str
    tank_id: str
    shift: str
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    animal_ids: List[str] = field(default_factory=list)
    total_litres: float = 0.0
    status: str = "IN_TANK"
    delivery_ticket_id: str | None = None


class MilkTraceabilityService:
    """
    End-to-end milk traceability chain:

        Cow Milking Entry
            -> Milking Shift
            -> Bulk Tank Batch
            -> Tanker Delivery Dispatch

    Veterinary non-milking directives are population/animal-state facts and
    are intentionally outside this traceability accounting object.
    """

    def __init__(self):
        self._batches: Dict[str, MilkTraceabilityBatch] = {}

    def create_batch(
        self,
        batch_id: str,
        tank_id: str,
        shift: str,
    ) -> MilkTraceabilityBatch:
        batch = MilkTraceabilityBatch(
            batch_id=batch_id,
            tank_id=tank_id,
            shift=shift,
        )
        self._batches[batch_id] = batch
        return batch

    def add_milking_to_batch(
        self,
        batch_id: str,
        animal_id: str,
        litres: float,
    ) -> MilkTraceabilityBatch | None:
        batch = self._batches.get(batch_id)

        if not batch:
            return None

        batch.animal_ids.append(animal_id)
        batch.total_litres += litres

        return batch

    def dispatch_delivery(
        self,
        batch_id: str,
        delivery_ticket_id: str,
    ) -> MilkTraceabilityBatch | None:
        batch = self._batches.get(batch_id)

        if not batch:
            return None

        batch.delivery_ticket_id = delivery_ticket_id
        batch.status = "DISPATCHED"

        return batch

    def trace_animal(
        self,
        animal_id: str,
    ) -> List[MilkTraceabilityBatch]:
        return [
            batch
            for batch in self._batches.values()
            if animal_id in batch.animal_ids
        ]
