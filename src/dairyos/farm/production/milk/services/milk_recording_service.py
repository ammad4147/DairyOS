from datetime import datetime
from dairyos.farm.production.milk.models.milk_record import MilkRecord



class MilkRecordingService:
    """
    Handles daily milk recording operations.
    """



    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def record_milk(
        self,
        record: MilkRecord,
    ):

        return self.repository.save(
            record
        )



    def total_milk(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ):
        """
        Sum milk litres. Optionally filter by date range.
        If no dates provided, sums ALL records (backward compatible).
        """

        records = self.repository.get_all()

        if date_from is not None:
            records = [
                r for r in records
                if r.recorded_at is not None and r.recorded_at >= date_from
            ]

        if date_to is not None:
            records = [
                r for r in records
                if r.recorded_at is not None and r.recorded_at <= date_to
            ]

        return sum(
            record.litres
            for record in records
        )
