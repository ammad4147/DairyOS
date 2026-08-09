from fastapi import APIRouter, Depends

from dairyos.api.dependencies import get_container


router = APIRouter(
    tags=["Dashboard"],
)


@router.get("/dashboard")
def get_dashboard(
    container=Depends(get_container),
):
    """Return the established dashboard contract from its projection service."""

    return container.dashboard_projection_service.project_api_contract(container)
