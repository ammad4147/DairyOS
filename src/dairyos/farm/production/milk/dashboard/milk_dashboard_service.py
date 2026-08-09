class MilkDashboardService:
    """
    Creates milk production dashboard summaries.

    Converts operational milk records
    into management information.
    """



    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def daily_summary(
        self,
    ):

        records = (
            self.repository.get_all()
        )


        total_litres = sum(
            record.litres
            for record
            in records
        )


        animals_milked = len(
            {
                record.animal_id
                for record
                in records
            }
        )


        average_per_animal = (

            total_litres / animals_milked

            if animals_milked

            else 0
        )


        sessions = list(
            {
                record.milking_session
                for record
                in records
            }
        )


        return {

            "milk_litres": total_litres,

            "animals_milked": animals_milked,

            "average_litres_per_animal":
                average_per_animal,

            "sessions": sessions,

            "status":
                "normal"
                if total_litres > 0
                else "attention",
        }
