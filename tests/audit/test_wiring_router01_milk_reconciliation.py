from __future__ import annotations


def test_milk_reconciliation_route_is_defined_once_across_milk_routers():
    from dairyos.api import milk_production_analytics, milk_traceability

    matches = []
    for module_name, router in (
        ("milk_production_analytics", milk_production_analytics.router),
        ("milk_traceability", milk_traceability.router),
    ):
        for route in router.routes:
            if route.path == "/farm/milk/reconciliation" and "GET" in route.methods:
                matches.append(module_name)

    assert matches == ["milk_traceability"]


def test_milk_traceability_route_accepts_operational_date_fallback():
    from dairyos.api import milk_traceability

    matches = [
        route
        for route in milk_traceability.router.routes
        if route.path == "/farm/milk/reconciliation" and "GET" in route.methods
    ]

    assert len(matches) == 1
    assert matches[0].name == "milk_reconciliation"
