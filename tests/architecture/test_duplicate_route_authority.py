"""Public paths with duplicate declarations have one documented owner."""

from dairyos.api.animal_passport import router as animal_passport_router
from dairyos.api.dairy_kpi import router as dairy_kpi_router
from dairyos.api.equipment_management import router as equipment_router
from dairyos.api.farm_data_entry import router as farm_router
from dairyos.api.farm_intelligence import router as farm_intelligence_router
from dairyos.api.milk_legacy_compat import router as milk_legacy_compat_router
from dairyos.api.milk_production_analytics import router as milk_analytics_router
from dairyos.api.milk_traceability import router as milk_traceability_router
from dairyos.app import app


def _routes(router, path: str, method: str):
    return [
        route
        for route in router.routes
        if str(getattr(route, "path", "")) == path
        and method.upper()
        in {str(item).upper() for item in (getattr(route, "methods", set()) or set())}
    ]


def test_shadowed_handlers_are_not_mounted_and_openapi_matches_active_owner():
    assert _routes(farm_router, "/farm/equipment", "GET") == []
    assert _routes(farm_router, "/farm/equipment", "POST") == []
    assert _routes(equipment_router, "/farm/equipment", "GET")
    assert _routes(equipment_router, "/farm/equipment", "POST")

    assert _routes(farm_intelligence_router, "/farm/animals/{animal_id}/passport", "GET") == []
    assert _routes(animal_passport_router, "/farm/animals/{animal_id}/passport", "GET")

    assert _routes(dairy_kpi_router, "/farm/kpis", "GET") == []
    assert _routes(farm_intelligence_router, "/farm/kpis", "GET")
    assert _routes(dairy_kpi_router, "/farm/kpis/overview", "GET")

    assert _routes(milk_legacy_compat_router, "/farm/milk/capacity", "GET") == []
    assert _routes(milk_traceability_router, "/farm/milk/capacity", "GET")

    assert _routes(milk_analytics_router, "/farm/milk/dispositions", "POST") == []
    assert _routes(milk_traceability_router, "/farm/milk/dispositions", "POST")

    operations = app.openapi()["paths"]
    assert operations["/farm/equipment"]["post"]["operationId"].startswith(
        "create_or_update_equipment_"
    )
    assert operations["/farm/animals/{animal_id}/passport"]["get"][
        "operationId"
    ].startswith("get_lifetime_passport_")
    assert operations["/farm/kpis"]["get"]["operationId"].startswith(
        "dairy_kpis_"
    )
    assert operations["/farm/milk/capacity"]["get"]["operationId"].startswith(
        "milk_capacity_"
    )
    assert operations["/farm/milk/dispositions"]["post"]["operationId"].startswith(
        "create_milk_disposition_"
    )
