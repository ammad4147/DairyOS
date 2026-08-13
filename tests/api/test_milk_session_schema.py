import pytest
from pydantic import ValidationError

from dairyos.api.farm_data_entry import MilkEntryRequest, _record
from dairyos.milk.models.milking_session import MilkingSession


class _MilkRepository:
    def __init__(self):
        self.record = None

    def save(self, record):
        self.record = record
        return record


class _RepositoryFactory:
    def __init__(self):
        self.repository = _MilkRepository()

    def milk(self):
        return self.repository

    def rollback(self):
        pass

    def close(self):
        pass


class _Gateway:
    def __init__(self):
        self.payload = None

    def record(self, *, input_type, payload, actor):
        self.payload = payload
        return type("Event", (), {"payload": {"input_type": input_type, "actor": actor}})()


class _Container:
    def __init__(self):
        self.repository_factory = _RepositoryFactory()
        self.input_gateway = _Gateway()


def test_milk_entry_requires_governed_milking_session():
    with pytest.raises(ValidationError):
        MilkEntryRequest(
            animal_id="AN-TEST-001",
            morning_yield=10.0,
        )

    entry = MilkEntryRequest(
        animal_id="AN-TEST-001",
        morning_yield=10.0,
        milking_session=MilkingSession.MORNING,
    )

    assert entry.milking_session is MilkingSession.MORNING


def test_milk_record_persists_session_and_publishes_same_value():
    container = _Container()

    result = _record(
        container,
        "milk_production",
        {
            "animal_id": "AN-TEST-001",
            "milking_session": "AFTERNOON",
            "morning_yield": 0.0,
            "afternoon_yield": 12.5,
            "evening_yield": 0.0,
            "total_yield": 12.5,
        },
    )

    assert container.repository_factory.repository.record.milking_session == "AFTERNOON"
    assert container.input_gateway.payload["milking_session"] == "AFTERNOON"
    assert result["input_type"] == "milk_production"
