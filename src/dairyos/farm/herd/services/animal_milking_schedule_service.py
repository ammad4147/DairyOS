from datetime import datetime


class AnimalMilkingScheduleService:
    """
    Converts animal milking frequency settings
    into expected operational milking sessions.

    The source of truth remains:
        Animal.milking_frequency

    This service only interprets the recorded
    operational instruction.

    It never automatically changes frequency.
    """


    FREQUENCY_MAP = {

        "TWICE_DAILY": [
            "MORNING",
            "EVENING",
        ],

        "THRICE_DAILY": [
            "MORNING",
            "AFTERNOON",
            "EVENING",
        ],

    }


    def get_expected_sessions(
        self,
        animal,
    ):
        """
        Returns expected milking sessions
        for the animal's current frequency.
        """

        frequency = (
            animal.milking_frequency
        )


        if not frequency:

            return []


        return self.FREQUENCY_MAP.get(
            frequency,
            [],
        )



    def get_schedule_snapshot(
        self,
        animal,
    ):
        """
        Returns operational read information.
        """

        return {

            "animal_id":
                animal.animal_id,

            "milking_frequency":
                animal.milking_frequency,

            "expected_sessions":
                self.get_expected_sessions(
                    animal
                ),

            "generated_at":
                datetime.utcnow(),

        }
