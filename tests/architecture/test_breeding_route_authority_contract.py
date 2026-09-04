"""Route contracts for the form-governed breeding lifecycle authority."""

from dairyos.app import app


def _routes(path: str, method: str):
    return [
        route
        for route in app.routes
        if str(getattr(route, "path", "")) == path
        and method in set(getattr(route, "methods", set()) or set())
    ]


def test_breeding_write_and_read_routes_have_one_governed_authority():
    post_routes = _routes("/farm/breeding", "POST")
    get_routes = _routes("/farm/breeding", "GET")

    assert len(post_routes) == 1
    assert len(get_routes) == 1
    assert post_routes[0].endpoint.__module__ == "dairyos.api.breeding_biology"
    assert get_routes[0].endpoint.__module__ == "dairyos.api.breeding_biology"


def test_reproductive_state_route_has_one_governed_authority():
    routes = _routes("/farm/animals/{animal_id}/reproduction", "GET")

    assert len(routes) == 1
    assert routes[0].endpoint.__module__ == "dairyos.api.breeding_biology"


def test_dashboard_remains_owned_by_dashboard_module():
    routes = _routes("/dashboard", "GET")

    assert len(routes) == 1
    assert routes[0].endpoint.__module__ == "dairyos.api.dashboard"
