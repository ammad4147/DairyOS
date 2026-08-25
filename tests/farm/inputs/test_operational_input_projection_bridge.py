from dairyos.farm.inputs.services.operational_input_projection_bridge import (
    OperationalInputProjectionBridge,
)


class FakeStateService:
    def __init__(self):
        self.events = []

    def handle(self, event):
        self.events.append(event)


def _project(input_type, payload):
    state_service = FakeStateService()
    bridge = OperationalInputProjectionBridge(
        state_service=state_service
    )

    event = bridge.project(
        type(
            "OperationalInputReceivedStub",
            (),
            {
                "payload": {
                    **payload,
                    "input_type": input_type,
                    "source": "farm_operator",
                    "actor": "TEST",
                }
            },
        )()
    )

    return event, state_service


def test_milk_projection_maps_canonical_vocabulary():
    event, state = _project(
        "milk_production",
        {
            "animal_id": "COW-001",
            "total_yield": 30.0,
            "milking_session": "MORNING",
        },
    )

    assert event.event_type == "milk_recorded"
    assert event.payload["total_yield"] == 30.0
    assert event.payload["litres"] == 30.0
    assert event.payload["milking_session"] == "MORNING"
    assert event.payload["session"] == "MORNING"
    assert event.payload["shift"] == "MORNING"
    assert state.events == [event]


def test_workforce_projection_preserves_canonical_fields():
    event, _ = _project(
        "workforce",
        {
            "worker_id": "WORKER-001",
            "activity": "milking",
        },
    )

    assert event.event_type == "workforce_activity_recorded"
    assert event.payload["worker_id"] == "WORKER-001"
    assert event.payload["activity"] == "milking"
    assert event.payload["metric_type"] == "WORKER-001"
    assert event.payload["value"] == "milking"


def test_inventory_projection_wraps_business_fields_in_details():
    event, _ = _project(
        "inventory",
        {
            "item": "Silage",
            "quantity": 440.0,
            "movement_type": "CONSUMPTION",
            "unit": "kg",
        },
    )

    assert event.event_type == "inventory_status_recorded"
    assert event.payload["item"] == "Silage"
    assert event.payload["quantity"] == 440.0
    assert event.payload["inventory_type"] == "Silage"
    assert event.payload["details"]["quantity"] == 440.0
    assert event.payload["details"]["movement_type"] == "CONSUMPTION"
    assert event.payload["details"]["unit"] == "kg"
    assert "input_type" not in event.payload["details"]
    assert "actor" not in event.payload["details"]


def test_equipment_projection_wraps_business_fields_in_details():
    event, _ = _project(
        "equipment",
        {
            "equipment_id": "MILKER-001",
            "activity": "inspection",
            "status": "OPERATIONAL",
            "running_hours": 120.5,
        },
    )

    assert event.event_type == "equipment_status_recorded"
    assert event.payload["equipment_id"] == "MILKER-001"
    assert event.payload["activity"] == "inspection"
    assert event.payload["details"]["activity"] == "inspection"
    assert event.payload["details"]["status"] == "OPERATIONAL"
    assert event.payload["details"]["running_hours"] == 120.5


def test_financial_projection_wraps_business_fields_in_details():
    event, _ = _project(
        "financial",
        {
            "transaction_type": "EXPENSE",
            "amount": 25000.0,
            "category": "Feed",
            "payment_method": "BANK",
            "counterparty": "Feed Supplier",
        },
    )

    assert event.event_type == "financial_status_recorded"
    assert event.payload["transaction_type"] == "EXPENSE"
    assert event.payload["financial_type"] == "EXPENSE"
    assert event.payload["amount"] == 25000.0
    assert event.payload["details"]["amount"] == 25000.0
    assert event.payload["details"]["category"] == "Feed"
    assert event.payload["details"]["payment_method"] == "BANK"
    assert event.payload["details"]["counterparty"] == "Feed Supplier"
    assert "input_type" not in event.payload["details"]
    assert "actor" not in event.payload["details"]


def test_unsupported_input_is_ignored():
    state_service = FakeStateService()
    bridge = OperationalInputProjectionBridge(
        state_service=state_service
    )

    event = bridge.project(
        type(
            "OperationalInputReceivedStub",
            (),
            {
                "payload": {
                    "input_type": "unsupported",
                    "source": "farm_operator",
                    "actor": "TEST",
                }
            },
        )()
    )

    assert event is None
    assert state_service.events == []
