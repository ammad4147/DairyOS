from dataclasses import dataclass
from datetime import date



@dataclass
class MilkRevenue:


    animal_id: str

    revenue_date: date

    litres: float

    price_per_litre: float



    @property
    def total_revenue(self):

        return (

            self.litres

            *

            self.price_per_litre

        )
