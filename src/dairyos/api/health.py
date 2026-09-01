from fastapi import APIRouter

router = APIRouter(
    tags=["Health"]
)


@router.get("/health")
def health():

    return {

        "system": "DairyOS",

        "status": "healthy",

        "runtime": "active",

    }

@router.get("/farm/health/summary")
def get_health_summary():
    """
    Returns herd health KPIs expected by the Health tab (camelCase).
    """
    # TODO: Replace with real aggregation from treatments / withdrawals / vaccinations / finance
    return {
        "activeTreatments": 0,
        "withdrawalCount": 0,
        "vaccinationCoverage": 0,
        "vetExpenses30Day": 0,
    }

