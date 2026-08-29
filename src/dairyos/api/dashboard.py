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

    # The RuntimeContainer exposes the exact repository instance owned by the
    # ApplicationRuntime. Dashboard must not reacquire another repository
    # instance from RepositoryFactory, or a disposition made through the
    # authoritative Animals surface can be invisible here until refresh/rebind.
    animal_repository = container.animal_repository
    finance_repository = container.finance_repository if hasattr(container, "finance_repository") else container.repository_factory.finance()

    active_animals = animal_repository.active_animals()
    finance_rows = finance_repository.get_all()
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
