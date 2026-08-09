from dataclasses import dataclass, field
from datetime import datetime, timezone

from dairyos.milk.models.milking_session import MilkingSession


@dataclass
class MilkingShift:

    shift_id: str

    session: MilkingSession

    expected_animals: list[str]

    completed_animals: list[str] = field(
        default_factory=list
    )

    operator: str = ""

    closed: bool = False

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def register_animal(
        self,
        animal_id: str
    ):

        if animal_id not in self.completed_animals:
            self.completed_animals.append(animal_id)


    def missing_animals(self):

        return [
            animal
            for animal in self.expected_animals
            if animal not in self.completed_animals
        ]


    def is_complete(self):

        return len(
            self.missing_animals()
        ) == 0


    def close_shift(
        self,
        operator: str
    ):

        if not self.is_complete():

            raise ValueError(
                "Cannot close incomplete milking shift"
            )

        self.operator = operator
        self.closed = True
