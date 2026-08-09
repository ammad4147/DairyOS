class AnimalHealthSummaryService:



    def build(

        self,

        animal_id,

        health_history,

        reproductive_history,

        signals

    ):

        return {

            "animal_id": animal_id,

            "health_history_count":

                len(health_history),

            "reproductive_history_count":

                len(reproductive_history),

            "active_health_signals":

                len(signals),

            "requires_review":

                len(signals) > 0

        }
