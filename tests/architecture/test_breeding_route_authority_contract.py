"""Route contracts for the form-governed breeding lifecycle authority."""

# Importing the application first applies its deliberate compatibility-route
# unmounting before these router objects are inspected.
from dairyos.app import app
from dairyos.api.animal_passport import router as animal_passport_router
from dairyos.api.breeding_biology import router as breeding_biology_router
from dairyos.api.command_center import router as command_router
from dairyos.api.dashboard import router as dashboard_router
from dairyos.api.farm_data_entry import router as farm_router
from dairyos.api.farm_planning import router as farm_planning_router


def _router_routes(router, path: str, method: str):
    wanted_method = method.upper()
    return [
        route
        for route in router.routes
        if str(getattr(route, "path", "")) == path
        and wanted_method
        in {str(item).upper() for item in (getattr(route, "methods", set()) or set())}
    ]


def test_public_breeding_paths_are_mounted():
    paths = app.openapi()["paths"]

    assert "post" in paths["/farm/breeding"]
    assert "get" in paths["/farm/breeding"]
    assert "get" in paths["/farm/animals/{animal_id}/reproduction"]
    assert "get" in paths["/dashboard"]


def test_breeding_write_and_read_routes_have_one_governed_owner():
    assert len(_router_routes(breeding_biology_router, "/farm/breeding", "POST")) == 1
    assert len(_router_routes(breeding_biology_router, "/farm/breeding", "GET")) == 1

    # Compatibility and command-center routers must not compete for the live
    # breeding write/read path.
    assert _router_routes(farm_router, "/farm/breeding", "POST") == []
    assert _router_routes(farm_router, "/farm/breeding", "GET") == []
    assert _router_routes(command_router, "/farm/breeding", "POST") == []
    assert _router_routes(command_router, "/farm/breeding", "GET") == []


def test_reproductive_state_route_has_one_governed_owner():
    assert len(
        _router_routes(
            breeding_biology_router,
            "/farm/animals/{animal_id}/reproduction",
            "GET",
        )
    ) == 1

    assert _router_routes(
        animal_passport_router,
        "/farm/animals/{animal_id}/reproduction",
        "GET",
    ) == []
    assert _router_routes(
        farm_planning_router,
        "/farm/animals/{animal_id}/reproduction",
        "GET",
    ) == []
    assert _router_routes(
        command_router,
        "/farm/animals/{animal_id}/reproduction",
        "GET",
    ) == []


def test_dashboard_remains_owned_by_dashboard_module():
    assert len(_router_routes(dashboard_router, "/dashboard", "GET")) == 1
    assert _router_routes(breeding_biology_router, "/dashboard", "GET") == []
    assert _router_routes(command_router, "/dashboard", "GET") == []