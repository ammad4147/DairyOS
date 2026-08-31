from dataclasses import asdict

from dairyos.platform.digital_twin.services.digital_twin_service import (
    DigitalTwinService,
)


class StubSync:
    def synchronize(self, **kwargs):
        return None


class StubRepository:
    def save(self, **kwargs):
        return None


def test_digital_twin_uses_explicit_forecast_and_scenario_inputs():

    service = DigitalTwinService(
        sync=StubSync(),
        repository=StubRepository(),
    )

    result = service.scenario(
        farm_id="farm",
        metric="MILK_LITERS",
        current_value=1000.0,
        scenario_name="Growth Case",
        parameter="milk",
        change_percent=12.0,
        growth_rate_percent=2.0,
        horizon_days=45,
        state={"source": "persisted"},
    )

    payload = asdict(result)

    assert payload["current_state"] == {"source": "persisted"}
    assert payload["forecast_summary"]
    assert payload["scenario_summary"]
    assert payload["scenario_summary"]["change_percent"] == 12.0
    assert payload["decision_signals"]


def test_digital_twin_does_not_inject_fixed_five_percent_signal():

    service = DigitalTwinService(
        sync=StubSync(),
        repository=StubRepository(),
    )

    result = service.scenario(
        farm_id="farm",
        metric="MILK_LITERS",
        current_value=1000.0,
        scenario_name="Flat Case",
        parameter="milk",
        change_percent=0.0,
        growth_rate_percent=0.0,
        horizon_days=30,
        state={},
    )

    signal = result.decision_signals[0]

    assert "0.0%" in signal.message
