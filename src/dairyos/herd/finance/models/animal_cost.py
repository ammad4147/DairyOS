from dataclasses import dataclass
from datetime import date



@dataclass
class AnimalCost:


    animal_id: str

    cost_date: date

    feed_cost: float

    health_cost: float

    breeding_cost: float



    @property
    def total_cost(self):

        return (

            self.feed_cost

            +

            self.health_cost

            +

            self.breeding_cost

        )
