from fastapi.testclient import TestClient

from dairyos.app import app
from dairyos.farm.operations.services.analytics_contract_service import (
    AnalyticsContractService,
)
from dairyos.farm.operations.services.reconciled_implementation_contract_service import (
    ReconciledImplementationContractService,
)


def test_analytics_catalog_is_backend_authoritative():
    body = AnalyticsContractService.catalog()

    assert body["contract_version"] == "1.0"
    assert body["synthetic_values"] is False
    assert body["frontend_calculation_authority"] is False

    for name, contract in body["analyses"].items():
        assert contract["authoritative_sources"], name
        assert contract["operational_date_basis"], name
        assert contract["completeness_requirements"], name


def test_analytics_routes_are_registered():
    routes = {
        route.path
        for route in app.routes
        if hasattr(route, "path")
    }

    catalog = AnalyticsContractService.catalog()

    for name, contract in catalog["analyses"].items():
        if contract["status"] != "AVAILABLE":
            continue

        assert contract["endpoint"] in routes, (
            f"{name}: {contract['endpoint']}"
        )


def test_reconciled_contract_exposes_analytics_and_cmp():
    catalog = ReconciledImplementationContractService.catalog()

    assert "analytics_contract" in catalog["capabilities"]
    assert "cmp" in catalog["capabilities"]

    assert (
        catalog["capabilities"]["analytics_contract"]
        ["authoritative_service"]
    )

    assert (
        catalog["capabilities"]["cmp"]
        ["authoritative_service"]
    )


def test_analytics_api_exposes_contract_catalog():
    client = TestClient(app)

    response = client.get("/farm/analytics/catalog")

    assert response.status_code == 200

    body = response.json()

    assert body["frontend_calculation_authority"] is False
    assert "yield" in body["analyses"]
    assert "sales" in body["analyses"]


def test_cmp_routes_are_registered():
    routes = {
        route.path
        for route in app.routes
        if hasattr(route, "path")
    }

    assert "/farm/cmp/scenarios" in routes
    assert "/farm/cmp/scenarios/{scenario_id}" in routes
