from dairyos.milk.models.milk_entry import MilkEntry
from dairyos.milk.models.milk_record import MilkRecord

from dairyos.milk.services.milk_record_service import (
    MilkRecordService
)

from dairyos.milk.services.milk_validation_service import (
    MilkValidationService
)



class MilkService:


    def __init__(self):

        self.record_service = MilkRecordService()

        self.validation_service = MilkValidationService()



    def record_milking(
        self,
        entry: MilkEntry
    ):

        entry.validate()


        record = MilkRecord(

            record_id=entry.entry_id,

            animal_id=entry.animal_id,

            session=entry.session,

            quantity_litres=entry.litres,

            operator=entry.operator,

        )


        return self.record_service.add_record(
            record
        )



    def daily_production(self):

        return self.record_service.daily_total()



    def animal_yield(
        self,
        animal_id: str
    ):

        return self.record_service.animal_daily_yield(
            animal_id
        )



    def session_records(
        self,
        session
    ):

        return self.record_service.records_by_session(
            session
        )
