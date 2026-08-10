from datetime import datetime, timezone


class MilkProductionIntelligenceService:
    """
    Read-only intelligence layer over live milk operational state.

    Does not create milk records.
    Does not modify operational state.

    Converts recorded milk facts into
    operational intelligence.
    """


    def __init__(
        self,
        operational_state_service,
    ):

        self.operational_state_service = (
            operational_state_service
        )


    def current_production_summary(
        self,
    ):

        state = (
            self.operational_state_service
            .get_state()
        )


        milk_status = state.milk_status


        total_litres = (
            state.milk_total()
        )


        shifts = {}


        for shift, data in milk_status.items():

            shifts[shift] = {

                "status":
                    data.get(
                        "status"
                    ),

                "litres":
                    data.get(
                        "litres",
                        0,
                    ),

                "animals_milked":
                    data.get(
                        "animals_milked",
                        0,
                    ),

                "operators":
                    list(
                        data.get(
                            "operators",
                            [],
                        )
                    ),

                "last_entry_time":
                    data.get(
                        "last_entry_time"
                    ),

            }


        return {

            "farm_id":
                state.farm_id,

            "operational_date":
                state.operational_date,

            "total_litres":
                total_litres,

            "shifts":
                shifts,

        }



    def litres_per_animal(
        self,
    ):

        state = (
            self.operational_state_service
            .get_state()
        )

        unique_animals = set()
        fallback_animal_count = 0

        for data in state.milk_status.values():
            animal_set = data.get("unique_animal_ids")
            if animal_set:
                unique_animals.update(animal_set)
            else:
                fallback_animal_count = max(
                    fallback_animal_count,
                    data.get("animals_milked", 0),
                )

        total_animals = len(unique_animals) if unique_animals else fallback_animal_count

        if total_animals == 0:

            return 0


        return (
            state.milk_total()
            /
            total_animals
        )



    def shift_status(
        self,
    ):

        state = (
            self.operational_state_service
            .get_state()
        )


        return {

            shift:
                data.get(
                    "status",
                    "unknown",
                )

            for shift, data

            in state.milk_status.items()

        }



    def production_heads_up(
        self,
    ):

        state = (
            self.operational_state_service
            .get_state()
        )


        notifications = []


        for shift, data in state.milk_status.items():

            if data.get("litres", 0) == 0:

                notifications.append(

                    {

                        "type":
                            "MILK_PRODUCTION_MISSING",

                        "shift":
                            shift,

                        "message":
                            f"No milk recorded for {shift} shift",

                    }

                )


        return notifications
