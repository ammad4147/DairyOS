from fastapi.testclient import TestClient

from dairyos.app import app
from dairyos.farm.operations.services.analytics_contract_service import (
    AnalyticsContractService,
)
from dairyos.farm.operations.services.reconciled_implementation_contract_service import (
    ReconciledImplementationContractService,
)


def _paths() -> set[str]:
    """Every publicly registered FastAPI route path.

    FastAPI 0.140+ keeps included routers behind internal route wrappers.
    The generated OpenAPI document is the stable application-level view of
    the routes actually mounted on the API.
    """
    return set(app.openapi()["paths"])


def test_analytics_catalog_is_backend_authoritative():
    body = AnalyticsContractService.catalog()

    assert body["contract_version"] == "1.0"
    assert body["synthetic_values"] is False
    assert body["frontend_calculation_authority"] is False

    for name, contract in body["analyses"].items():
        assert contract["authoritative_sources"], name
        assert contract["operational_date_basis"], name
        assert contract["completeness_requirements"], name


def test_available_analytics_use_registered_live_routes():
    paths = _paths()
    catalog = AnalyticsContractService.catalog()

    for name, contract in catalog["analyses"].items():
        if contract["status"] != "AVAILABLE":
            continue

        endpoint = contract["endpoint"]

        assert endpoint
        assert endpoint in paths, f"{name}: {endpoint}"


def test_thi_contract_matches_live_heat_stress_route():
    contract = AnalyticsContractService.catalog()["analyses"]["thi"]

    assert contract["status"] == "AVAILABLE"
    assert contract["endpoint"] == "/farm/heat-stress/intelligence"


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
    assert "thi" in body["analyses"]


def test_cmp_routes_are_registered():
    paths = _paths()

    assert "/farm/cmp/scenarios" in paths
    assert "/farm/cmp/scenarios/{scenario_id}" in paths
