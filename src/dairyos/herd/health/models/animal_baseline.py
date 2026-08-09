from dataclasses import dataclass


@dataclass
class AnimalBaseline:

    animal_id: str

    average_milk_yield: float

    average_feed_intake: float

    average_temperature: float
