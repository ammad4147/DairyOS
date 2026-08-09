from ..models.daily_operations import DailyOperations



class DailyOperationsService:



    def create_daily_status(

        self,

        milk_target,

        milk_actual,

        completed_tasks,

        pending_tasks

    ):


        if milk_actual >= milk_target:

            production_status = "ON TARGET"

        else:

            production_status = "ATTENTION"



        if pending_tasks > 0:

            overall_status = "MONITOR"

        else:

            overall_status = "STABLE"



        return DailyOperations(

            milk_target,

            milk_actual,

            completed_tasks,

            pending_tasks,

            production_status,

            overall_status

        )
