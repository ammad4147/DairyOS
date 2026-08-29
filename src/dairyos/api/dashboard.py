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
    payload = container.dashboard_projection_service.project_api_contract(container)

    active_animals = container.repository_factory.animal().active_animals()
    finance_rows = container.repository_factory.finance().get_all()
    receivables = sum(
        float(row.amount or 0)
        for row in finance_rows
        if str(row.status or "").upper() == "RECEIVABLE"
    )

    dashboard = payload.setdefault("dashboard", {})
    dashboard["finance"] = {
        "receivables": receivables,
        "receivable_count": sum(
            1
            for row in finance_rows
            if str(row.status or "").upper() == "RECEIVABLE"
        ),
    }
    dashboard["animals"] = {
        **dashboard.get("animals", {}),
        "total": len(active_animals),
    }

    payload["animals"] = {
        **payload.get("animals", {}),
        "total": len(active_animals),
    }
    payload["finance"] = dashboard["finance"]
    return payload
