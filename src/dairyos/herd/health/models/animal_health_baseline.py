from dataclasses import dataclass


@dataclass
class AnimalHealthBaseline:

    animal_id: str

    average_milk_yield: float

    average_feed_intake: float

    average_temperature: float

    average_activity_level: float

    observation_period_days: int
