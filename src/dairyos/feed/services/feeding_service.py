from dairyos.feed.models import FeedingRecord


class FeedingService:

    def __init__(self):
        self.records = []

    def add_record(
        self,
        record: FeedingRecord,
    ):

        self.records.append(record)

    def get_records(self):

        return self.records

    def get_group_records(
        self,
        animal_group: str,
    ):

        return [
            record
            for record in self.records
            if record.animal_group == animal_group
        ]
