from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class OperationalContextBuilder:
    """
    Converts FarmOperationalState into
    intelligence-readable operational context.

    Rules:
    - Read only.
    - No operational mutation.
    - No decision execution.
    """


    def build(
        self,
        state: FarmOperationalState,
    ):

        return {

            "farm_id":
                state.farm_id,


            "operational_date":
                state.operational_date,


            "milk_total":
                state.milk_total(),


            "feed_total":
                state.feed_total(),


            "health_alert_count":
                state.health_alert_count(),


            "open_task_count":
                len(
                    state.open_tasks
                ),


            "completed_task_count":
                len(
                    state.completed_tasks
                ),


            "heads_up_count":
                state.heads_up_count(),


            "exception_count":
                len(
                    state.exceptions
                ),


            "operational_status": (
                    state.operational_status()
                    .lower()
                ),


            "operational_freshness":
                dict(
                    state.operational_freshness
                ),

        }
