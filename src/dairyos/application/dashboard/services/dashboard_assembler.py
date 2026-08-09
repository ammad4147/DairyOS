from datetime import date

from ..integrations.domain_dashboard_adapter import (
    DomainDashboardAdapter,
)

from ..integrations.event_dashboard_adapter import (
    EventDashboardAdapter,
)

from ..models.farm_today import (
    FarmTodaySnapshot,
)

from ..models.dashboard_alert import (
    DashboardAlert,
)

from ..models.dashboard_action import (
    DashboardAction,
)



class DashboardAssembler:
    """
    Converts operational information
    into dashboard read projections.

    Read side only.

    Does not:
        - create tasks
        - execute actions
        - mutate operational state
    """


    def __init__(
        self,
        adapter: DomainDashboardAdapter | None = None,
        event_adapter: EventDashboardAdapter | None = None,
        daily_milk_production_command_view_service=None,
        operational_state_service=None,
    ):

        self.adapter = (
            adapter
            if adapter
            else DomainDashboardAdapter()
        )


        self.event_adapter = (
            event_adapter
            if event_adapter
            else EventDashboardAdapter()
        )


        self.daily_milk_production_command_view_service = (
            daily_milk_production_command_view_service
        )


        self.operational_state_service = (
            operational_state_service
        )



    def assemble_today(
        self,
    ) -> FarmTodaySnapshot:


        snapshot = FarmTodaySnapshot(

            snapshot_date=date.today(),


            total_animals=(
                self.adapter
                .get_total_animals()
            ),


            milking_animals=(
                self.adapter
                .get_milking_animals()
            ),


            dry_animals=(
                self.adapter
                .get_dry_animals()
            ),


            milk_total_litres=(
                self.adapter
                .get_milk_total()
            ),


            milk_command=(
                self.adapter
                .get_milk_command()
            ),


            feed_consumption_kg=(
                self.adapter
                .get_feed_consumption()
            ),


            pending_tasks=(
                self.adapter
                .get_pending_tasks()
            ),


            overdue_tasks=(
                self.adapter
                .get_overdue_tasks()
            ),


            daily_milk_production_command_view=(
                self._get_daily_milk_view()
            ),


            activities=(
                self.event_adapter
                .get_activities()
            ),

        )


        self._project_heads_up(
            snapshot
        )


        self._project_task_actions(
            snapshot
        )


        return snapshot



    def _get_daily_milk_view(
        self,
    ):

        if (
            self.daily_milk_production_command_view_service
            is None
        ):

            return {}


        return (
            self.daily_milk_production_command_view_service
            .summary()
        )



    def _project_heads_up(
        self,
        snapshot,
    ):

        if self.operational_state_service is None:

            return


        state = (
            self.operational_state_service
            .get_state()
        )


        for notification in state.heads_up_notifications:

            snapshot.alerts.append(

                DashboardAlert(

                    title=notification.get(
                        "notification_type",
                        "OPERATIONAL_ALERT",
                    ),

                    message=notification.get(
                        "message",
                        "",
                    ),

                    severity=notification.get(
                        "severity",
                        "WARNING",
                    ),

                    source="operational_heads_up",

                )

            )



    def _project_task_actions(
        self,
        snapshot,
    ):

        if self.operational_state_service is None:

            return


        state = (
            self.operational_state_service
            .get_state()
        )


        for task in state.open_tasks:

            priority = task.get(
                "priority",
                "NORMAL",
            )


            attention_required = (

                priority in (
                    "HIGH",
                    "CRITICAL",
                )

                or

                task.get(
                    "status",
                    "OPEN",
                )
                == "OPEN"

            )


            if not attention_required:

                continue


            snapshot.actions.append(

                DashboardAction(

                    title="Operational task requires attention",

                    description=task.get(
                        "description",
                        "",
                    ),

                    source="task_intelligence",

                    action_type="TASK_REVIEW",

                    priority=priority,

                    responsible_role=task.get(
                        "assigned_to",
                        "",
                    ),

                )

            )
