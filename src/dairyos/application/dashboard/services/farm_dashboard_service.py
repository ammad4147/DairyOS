from ..models.farm_today import FarmTodaySnapshot
from ..context.dashboard_context import DashboardContext
from .dashboard_assembler import DashboardAssembler


class FarmDashboardService:
    """
    Application service exposing operational dashboard data.

    Bridges operational domain information
    into dashboard-safe application views.
    """

    def __init__(
        self,
        assembler: DashboardAssembler | None = None,
        operations_timeline_service=None,
    ):

        self.assembler = (
            assembler
            if assembler
            else DashboardAssembler()
        )

        self.operations_timeline_service = (
            operations_timeline_service
        )


    def get_today(
        self,
        context: DashboardContext | None = None,
    ) -> FarmTodaySnapshot:
        """
        Returns today's operational dashboard snapshot.

        Existing dashboard behaviour is preserved.
        """

        return (
            self.assembler
            .assemble_today()
        )


    def get_operational_timeline(
        self,
    ):
        """
        Returns farm operational events
        recorded during the farm day.
        """

        if not self.operations_timeline_service:
            return []

        return (
            self.operations_timeline_service
            .get_timeline()
        )
