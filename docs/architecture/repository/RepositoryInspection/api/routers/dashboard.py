from fastapi import APIRouter

from dairyos.operations.dashboard.services.dashboard_builder_service import (
    DashboardBuilderService,
)

from dairyos.operations.dashboard.services.dashboard_summary_service import (
    DashboardSummaryService,
)


router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)


@router.get("/dashboard")
def operations_dashboard():

    dashboard = DashboardBuilderService().build(
        dashboard_id="DEFAULT",
        open_issue_count=0,
        resolution_rate=100.0,
        effectiveness_score=100.0,
    )


    return DashboardSummaryService().summarize(
        dashboard
    )
