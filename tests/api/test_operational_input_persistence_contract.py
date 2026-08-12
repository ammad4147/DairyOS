import pytest
from fastapi import HTTPException

from dairyos.api.farm_data_entry import _record


class _Gateway:
    def __init__(self, order):
        self.order = order

    def record(self, *, input_type, payload, actor):
        self.order.append("event")
        return type("Event", (), {"payload": {"input_type": input_type, "actor": actor}})()


class _MilkRepository:
    def __init__(self, order, fail=False):
        self.order = order
        self.fail = fail

    def save(self, record):
        if self.fail:
            raise RuntimeError("domain persistence failure")
        self.order.append("domain")


class _RepositoryFactory:
    def __init__(self, order, fail=False):
        self.order = order
        self.fail = fail

    def milk(self):
        return _MilkRepository(self.order, fail=self.fail)

    def rollback(self):
        self.order.append("rollback")

    def close(self):
        self.order.append("close")


class _Container:
    def __init__(self, order, fail=False):
        self.repository_factory = _RepositoryFactory(order, fail=fail)
        self.input_gateway = _Gateway(order)


def test_repository_backed_input_persists_before_event():
    order = []
    container = _Container(order)

    result = _record(
        container,
        "milk_production",
        {
            "animal_id": "AN-TEST-001",
            "morning_yield": 10.0,
            "afternoon_yield": 5.0,
            "evening_yield": 5.0,
            "total_yield": 20.0,
        },
    )

    assert order == ["domain", "event"]
    assert result["input_type"] == "milk_production"


def test_repository_failure_does_not_publish_operational_event():
    order = []
    container = _Container(order, fail=True)

    with pytest.raises(HTTPException) as exc:
        _record(
            container,
            "milk_production",
            {
                "animal_id": "AN-TEST-002",
                "morning_yield": 10.0,
                "afternoon_yield": 5.0,
                "evening_yield": 5.0,
                "total_yield": 20.0,
            },
        )

    assert exc.value.status_code == 500
    assert order == ["rollback"]
