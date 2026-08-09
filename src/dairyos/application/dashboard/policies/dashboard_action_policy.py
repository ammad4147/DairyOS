from dairyos.application.dashboard.models.dashboard_action import (
    DashboardAction,
)

from dairyos.application.dashboard.models.dashboard_action_status import (
    DashboardActionStatus,
)

from dairyos.application.dashboard.models.farm_today import (
    FarmTodaySnapshot,
)


class DashboardActionPolicy:
    """
    Determines operational actions
    from dashboard conditions.

    This is a presentation decision layer.

    Domain rules remain inside
    operational services.
    """

    def generate(
        self,
        snapshot: FarmTodaySnapshot,
    ) -> list[DashboardAction]:

        actions = []

        if snapshot.overdue_tasks > 0:

            actions.append(

                DashboardAction(

                    title="Review overdue tasks",

                    description=(
                        f"{snapshot.overdue_tasks} "
                        "operational tasks require attention"
                    ),

                    status=DashboardActionStatus.WARNING,

                    source="dashboard",

                )

            )

            return actions


        if snapshot.pending_tasks > 0:

            actions.append(

                DashboardAction(

                    title="Complete pending tasks",

                    description=(
                        f"{snapshot.pending_tasks} "
                        "tasks are awaiting completion"
                    ),

                    status=DashboardActionStatus.PENDING,

                    source="dashboard",

                )

            )

            return actions


        if snapshot.milk_total_litres <= 0:

            actions.append(

                DashboardAction(

                    title="Verify milk recording",

                    description=(
                        "No milk production recorded today"
                    ),

                    status=DashboardActionStatus.WARNING,

                    source="dashboard",

                )

            )

        return actions
