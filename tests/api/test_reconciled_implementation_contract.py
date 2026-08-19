from dairyos.app import app
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


def test_every_live_or_extended_capability_has_a_live_route():
    paths = _paths()
    catalog = ReconciledImplementationContractService.catalog()

    for name, contract in catalog["capabilities"].items():
        status = contract["status"]
        route = contract["route"]

        if status in {"LIVE", "EXTEND"}:
            assert route is not None, (
                f"{name} is {status} but has no authoritative route."
            )
            assert route in paths, (
                f"{name} is {status} but route {route!r} is not registered."
            )


def test_deferred_or_retired_capabilities_are_explicit():
    catalog = ReconciledImplementationContractService.catalog()

    for name, contract in catalog["capabilities"].items():
        status = contract["status"]

        assert status in {
            "LIVE",
            "EXTEND",
            "DEFER",
            "RETIRE",
        }, f"{name} has invalid capability status {status!r}"

        if status in {"DEFER", "RETIRE"}:
            assert (
                contract.get("next_dependency")
                or contract.get("reason")
            ), f"{name} is {status} without documented disposition."


def test_no_capability_uses_frontend_as_authority():
    catalog = ReconciledImplementationContractService.catalog()

    assert catalog["frontend_calculation_authority"] is False

    for name, contract in catalog["capabilities"].items():
        assert contract["authoritative_service"], (
            f"{name} has no authoritative backend service."
        )


def test_required_reconciliation_capabilities_are_present():
    catalog = ReconciledImplementationContractService.catalog()
    names = set(catalog["capabilities"])

    required = {
        "farm_identity_settings",
        "animal_passport",
        "effective_milking_schedule",
        "milk_execution_intelligence",
        "milk_reconciliation",
        "milk_dispositions",
        "analytics_contract",
        "cmp",
        "dashboard_read_model",
    }

    assert required.issubset(names)
