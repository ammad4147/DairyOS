class AnimalHealthTimelineService:



    def build(

        self,

        animal_id,

        historical_records,

        current_records

    ):

        return {

            "animal_id": animal_id,

            "historical_records": historical_records,

            "current_records": current_records,

            "history_available":

                len(historical_records) > 0

        }
