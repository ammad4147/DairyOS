from dairyos.milk.models.milk_entry import MilkEntry
from dairyos.milk.models.milking_session import MilkingSession


class MilkEntryService:


    def __init__(self):

        self.entries: list[MilkEntry] = []


    def record_entry(
        self,
        entry: MilkEntry
    ):

        entry.validate()

        self.entries.append(entry)


    def get_entries(self):

        return self.entries


    def total_litres(self):

        return sum(
            e.litres
            for e in self.entries
        )


    def session_total(
        self,
        session: MilkingSession
    ):

        return sum(
            e.litres
            for e in self.entries
            if e.session == session
        )


    def animal_total(
        self,
        animal_id: str
    ):

        return sum(
            e.litres
            for e in self.entries
            if e.animal_id == animal_id
        )
