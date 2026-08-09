from dairyos.farm.production.milk.models.milk_record import (
    MilkRecord,
)



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
    ):

        return sum(
            record.litres
            for record
            in self.repository.get_all()
        )
