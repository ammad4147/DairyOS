from dairyos.farm.production.milk.models.milk_record import (
    MilkRecord,
)



class MilkRepository:
    """
    Temporary milk record storage.

    Database adapter will replace this later.
    """



    def __init__(
        self,
    ):

        self.records = []



    def save(
        self,
        record: MilkRecord,
    ):

        self.records.append(
            record
        )

        return record



    def get_all(
        self,
    ):

        return self.records
