from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DailyMilkRegister:


    register_id: str

    date: str

    entries: list = field(
        default_factory=list
    )

    verified: bool = False

    verified_by: str = ""


    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def add_entry(
        self,
        entry
    ):

        self.entries.append(
            entry
        )


    def total_litres(self):

        return sum(
            e.litres
            for e in self.entries
        )


    def animals_recorded(self):

        return len(
            set(
                e.animal_id
                for e in self.entries
            )
        )


    def verify(
        self,
        operator
    ):

        self.verified = True

        self.verified_by = operator
