from dairyos.milk.models.farm_milking_day import FarmMilkingDay


class MilkDeploymentService:


    def start_day(
        self,
        farm_id,
        date
    ):

        return FarmMilkingDay(
            farm_id=farm_id,
            date=date
        )


    def assign_team(
        self,
        day,
        workers
    ):

        for worker in workers:

            day.assign_worker(
                worker
            )


    def close_session(
        self,
        day,
        session
    ):

        day.complete_session(
            session
        )


    def ready_for_closure(
        self,
        day
    ):

        return day.operational_status()
