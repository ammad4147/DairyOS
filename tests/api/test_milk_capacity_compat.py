from datetime import date
from types import SimpleNamespace

from dairyos.api import milk_legacy_compat
from dairyos.app import app


def test_capacity_route_is_registered_with_the_traceability_owner():
    operation = app.openapi()["paths"]["/farm/milk/capacity"]["get"]
    assert operation["operationId"] == "milk_capacity_farm_milk_capacity_get"
    through_date = next(
        parameter
        for parameter in operation["parameters"]
        if parameter["name"] == "through_date"
    )
    assert through_date["required"] is False


def test_legacy_capacity_adapter_remains_callable_for_internal_compatibility():
    assert callable(milk_legacy_compat.milk_capacity)


def test_capacity_route_uses_authoritative_capacity_service(monkeypatch):
    factory = object()
    container = SimpleNamespace(repository_factory=factory)
    seen = {}

    def fake_capacity(through_date, *, exclude_disposition_id=None, factory=None):
        seen["through_date"] = through_date
        seen["exclude_disposition_id"] = exclude_disposition_id
        seen["factory"] = factory
        return {
            "recorded_production_litres": 318.0,
            "ordinary_accounted_litres": 215.0,
            "available_saleable_litres": 73.0,
        }

    monkeypatch.setattr(
        milk_legacy_compat,
        "overall_saleable_capacity",
        fake_capacity,
    )

    result = milk_legacy_compat.milk_capacity(
        through_date=date(2026, 9, 30),
        container=container,
    )

    assert result["available_saleable_litres"] == 73.0
    assert seen == {
        "through_date": date(2026, 9, 30),
        "exclude_disposition_id": None,
        "factory": factory,
    }
