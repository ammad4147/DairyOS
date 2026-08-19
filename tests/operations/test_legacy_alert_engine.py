from dairyos.alerts.engine import AlertEngine
from dairyos.domain.events import Event


class FakeFindingService:
    def __init__(self):
        self.calls = []

    def raise_or_update(self, **kwargs):
        self.calls.append(kwargs)
        return object()


def test_legacy_low_milk_alert_becomes_operational_finding():
    service = FakeFindingService()
    engine = AlertEngine(finding_service=service)

    engine.handle_event(
        Event(
            name="MilkRecorded",
            payload={
                "animal_id": "TD-001",
                "milking_session": "MORNING",
                "quantity": 0.5,
            },
        )
    )

    assert len(service.calls) == 1
    finding = service.calls[0]
    assert finding["source_module"] == "MILK"
    assert finding["severity"] == "HIGH"
    assert finding["subject_id"] == "TD-001"
    assert finding["route"] == "milk"
    assert finding["dedupe_key"] == "LOW_MILK:TD-001:MORNING"


def test_legacy_alert_engine_ignores_normal_milk_recording():
    service = FakeFindingService()
    engine = AlertEngine(finding_service=service)

    engine.handle_event(
        Event(
            name="MilkRecorded",
            payload={
                "animal_id": "TD-001",
                "milking_session": "MORNING",
                "quantity": 12.0,
            },
        )
    )

    assert service.calls == []
