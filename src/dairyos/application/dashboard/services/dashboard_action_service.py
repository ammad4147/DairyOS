from dairyos.application.dashboard.models.dashboard_action import (
    DashboardAction,
)

from dairyos.application.dashboard.services.farm_dashboard_service import (
    FarmDashboardService,
)

from dairyos.application.dashboard.policies.dashboard_action_policy import (
    DashboardActionPolicy,
)


class DashboardActionService:
    """
    Application service generating
    dashboard operational actions.
    """


    def __init__(
        self,
        dashboard_service: FarmDashboardService,
        policy: DashboardActionPolicy | None = None,
    ):

        self.dashboard_service = dashboard_service

        self.policy = (
            policy
            if policy
            else DashboardActionPolicy()
        )


    def get_actions(self) -> list[DashboardAction]:

        snapshot = (
            self.dashboard_service
            .get_today()
        )

        return (
            self.policy
            .generate(snapshot)
        )
