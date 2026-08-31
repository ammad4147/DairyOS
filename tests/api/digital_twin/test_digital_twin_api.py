from datetime import date, datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from dairyos.api.dependencies import get_container
from dairyos.api.digital_twin.router import router


class StubAnimalRepository:
    def get_all(self):
        return [
            SimpleNamespace(active=True),
            SimpleNamespace(active=True),
            SimpleNamespace(active=False),
        ]


class StubMilkRepository:
    def get_all(self):
        return [
            SimpleNamespace(
                production_date=date.today(),
                total_yield=120.0,
            ),
            SimpleNamespace(
                production_date=date.today(),
                total_yield=80.0,
            ),
            SimpleNamespace(
                production_date=date.today(),
                total_yield=50.0,
            ),
        ]


class StubFeedRepository:
    def get_all(self):
        return [
            SimpleNamespace(
                feeding_date=date.today(),
                quantity_kg=25.0,
            ),
            SimpleNamespace(
                feeding_date=date.today(),
                quantity_kg=15.0,
            ),
        ]


class StubRepositoryFactory:
    def animal(self):
        return StubAnimalRepository()

    def milk(self):
        return StubMilkRepository()

    def feed(self):
        return StubFeedRepository()


class StubContainer:
    repository_factory = StubRepositoryFactory()


class EmptyMilkRepository:
    def get_all(self):
        return []


class EmptyFactory(StubRepositoryFactory):
    def milk(self):
        return EmptyMilkRepository()


class EmptyContainer:
    repository_factory = EmptyFactory()


app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_container] = lambda: StubContainer()
client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_container_override():
    app.dependency_overrides[get_container] = lambda: StubContainer()
    yield
    app.dependency_overrides[get_container] = lambda: StubContainer()


def test_baseline_endpoint():
    response = client.get(
        "/farm/digital-twin/baseline",
        params={"metric": "MILK_LITERS", "days": 30},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metric"] == "MILK_LITERS"
    assert payload["baseline_value"] == 250.0
    assert payload["data_status"] == "LIVE_PERSISTED_DATA"


def test_scenario_endpoint():
    response = client.post(
        "/farm/digital-twin/scenario",
        json={
            "metric": "MILK_LITERS",
            "scenario_name": "Milk growth",
            "parameter": "milk",
            "change_percent": 10,
            "growth_rate_percent": 0,
            "horizon_days": 30,
            "baseline_period_days": 30,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metric"] == "MILK_LITERS"
    assert payload["baseline_value"] == 250.0
    assert payload["scenario_change_percent"] == 10
    assert payload["digital_twin"]["scenario_summary"]["change_percent"] == 10.0


def test_negative_scenario_on_zero_baseline_is_rejected():
    app.dependency_overrides[get_container] = lambda: EmptyContainer()

    response = client.post(
        "/farm/digital-twin/scenario",
        json={
            "metric": "MILK_LITERS",
            "scenario_name": "Negative",
            "parameter": "milk",
            "change_percent": -10,
            "horizon_days": 30,
            "baseline_period_days": 30,
        },
    )

    assert response.status_code == 422
