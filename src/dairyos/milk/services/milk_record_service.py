from dairyos.milk.models.milk_record import MilkRecord
from dairyos.milk.models.milking_session import MilkingSession


class MilkRecordService:


    def __init__(self):

        self.records: list[MilkRecord] = []


    def add_record(
        self,
        record: MilkRecord
    ):

        record.validate()

        self.records.append(
            record
        )

        return record



    def get_records(self):

        return self.records



    def daily_total(self):

        return sum(

            record.quantity_litres

            for record in self.records

        )



    def animal_daily_yield(
        self,
        animal_id: str
    ):

        return sum(

            record.quantity_litres

            for record in self.records

            if record.animal_id == animal_id

        )



    def records_by_session(
        self,
        session: MilkingSession
    ):

        return [

            record

            for record in self.records

            if record.session == session

        ]
