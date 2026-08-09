from __future__ import annotations

from dairyos.application.application_runtime import ApplicationRuntime

from dairyos.application.dashboard.services.dashboard_assembler import (
    DashboardAssembler,
)

from dairyos.application.dashboard.services.command_center_service import (
    CommandCenterService,
)

from dairyos.application.dashboard.integrations.domain_dashboard_adapter import (
    DomainDashboardAdapter,
)

from dairyos.application.dashboard.integrations.event_dashboard_adapter import (
    EventDashboardAdapter,
)


class DashboardFactory:
    """
    Dashboard composition adapter.

    ApplicationRuntime is the sole application composition root.

    DashboardFactory consumes an already-composed ApplicationRuntime
    and must never construct another application graph.

    The class-level create() method retains the historical
    compatibility surface by creating the canonical ApplicationRuntime
    when no runtime is explicitly supplied.
    """

    @classmethod
    def create(
        cls,
        runtime: ApplicationRuntime | None = None,
    ):
        if runtime is None:
            runtime = ApplicationRuntime()

        return cls(runtime)

    def __init__(
        self,
        runtime: ApplicationRuntime,
        command_center_service: CommandCenterService | None = None,
    ):

        if runtime is None:
            raise ValueError(
                "DashboardFactory requires an ApplicationRuntime."
            )

        self.runtime = runtime

        domain_adapter = DomainDashboardAdapter(
            operations_runtime=runtime.farm_operations_runtime,
            animal_repository=runtime.animal_repository,
            animal_intelligence_service=(
                runtime.animal_intelligence_service
            ),
        )

        event_adapter = EventDashboardAdapter(
            event_repository=runtime.operational_event_repository,
            operations_runtime=runtime.farm_operations_runtime,
        )

        self.assembler = DashboardAssembler(
            adapter=domain_adapter,
            event_adapter=event_adapter,
            daily_milk_production_command_view_service=(
                runtime.daily_milk_production_command_view_service
            ),
            operational_state_service=(
                runtime.operational_state_service
            ),
        )

        self.command_center_service = command_center_service

        self.state_query_service = (
            runtime.operational_state_query_service
        )

        self.builder_service = (
            runtime.dashboard_builder_service
        )

        self.summary_service = (
            runtime.dashboard_summary_service
        )

    def get_today(self):

        return self.get_farm_today_snapshot()

    def get_command_center_snapshot(self):

        if self.command_center_service is not None:
            return (
                self.command_center_service
                .get_snapshot()
            )

        operational_command_center = (
            self.runtime
            .operational_command_center_service
            .get_snapshot()
        )

        projection = (
            self.runtime
            .command_center_projection_service
            .build_view(
                operational_command_center=(
                    operational_command_center
                )
            )
        )

        if hasattr(projection, "__dict__"):
            return projection.__dict__.copy()

        return projection

    def get_dashboard_summary(
        self,
        context=None,
    ):

        state = (
            self.state_query_service
            .get_current_state()
        )

        dashboard = (
            self.builder_service
            .build(
                dashboard_id=state.farm_id,
                open_issue_count=(
                    state.exception_count
                    +
                    state.open_task_count
                ),
                resolution_rate=(
                    (
                        state.completed_task_count
                        /
                        (
                            state.completed_task_count
                            + state.open_task_count
                        )
                    )
                    * 100
                    if (
                        state.completed_task_count
                        + state.open_task_count
                    ) > 0
                    else 0.0
                ),
                effectiveness_score=80.0,
                daily_milk_production_command_view=(
                    state.daily_milk_production_command_view
                ),
                heads_up_notifications=(
                    state.heads_up_notifications
                ),
                task_intelligence=(
                    state.task_intelligence
                ),
                open_tasks=(
                    state.open_tasks
                ),
                completed_tasks=(
                    state.completed_tasks
                ),
                readiness_status=(
                    state.readiness_status
                ),
                readiness_risks=(
                    state.readiness_risks
                ),
                execution_status=(
                    state.execution_status
                ),
                execution_details=(
                    state.execution_details
                ),
            )
        )

        return (
            self.summary_service
            .summarize(
                dashboard
            )
        )

    def get_farm_today_snapshot(
        self,
    ):

        return (
            self.assembler
            .assemble_today()
        )