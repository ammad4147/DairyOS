from dataclasses import dataclass
from datetime import date



@dataclass
class MilkRecord:


    animal_id: str

    production_date: date

    morning_litres: float

    evening_litres: float



    @property
    def total_litres(self):

        return (

            self.morning_litres

            +

            self.evening_litres

        )
