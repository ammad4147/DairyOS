from dataclasses import dataclass


@dataclass
class DailyMilkBoard:

    date: str

    morning_litres: float = 0

    afternoon_litres: float = 0

    evening_litres: float = 0

    animals_milked: int = 0

    expected_animals: int = 0


    @property
    def total_litres(self):

        return (
            self.morning_litres
            +
            self.afternoon_litres
            +
            self.evening_litres
        )


    @property
    def completion_percentage(self):

        if self.expected_animals == 0:

            return 0

        return round(
            (
                self.animals_milked
                /
                self.expected_animals
            )
            * 100,
            2
        )


    @property
    def average_yield(self):

        if self.animals_milked == 0:

            return 0

        return round(
            self.total_litres
            /
            self.animals_milked,
            2
        )
