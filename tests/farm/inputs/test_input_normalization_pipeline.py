from dairyos.runtime.container import RuntimeContainer


def test_milk_alias_normalization_pipeline():

    container = RuntimeContainer()

    event = (
        container.input_gateway.record_milk(
            payload={
                "animal_id": "TEST-COW-100",
                "litres": 30.0,
            },
            actor="TEST",
        )
    )

    assert event.input_type == "milk_production"

    assert event.payload["animal_id"] == "TEST-COW-100"

    assert event.payload["total_yield"] == 30.0



def test_feed_alias_normalization_pipeline():

    container = RuntimeContainer()

    event = (
        container.input_gateway.record_feed(
            payload={
                "feed_type": "TMR",
                "quantity": 40.0,
            },
            actor="TEST",
        )
    )

    assert event.input_type == "feeding"

    assert event.payload["feed_type"] == "TMR"

    assert event.payload["quantity_kg"] == 40.0


def test_vaccination_input_is_registered_and_persistable():

    container = RuntimeContainer()

    event = container.input_gateway.record(
        input_type="vaccination",
        payload={
            "animal_id": "TEST-COW-100",
            "vaccine": "FMD",
            "administered_date": "2026-09-01",
            "next_due_date": "2026-09-01",
            "status": "COMPLETED",
        },
        actor="TEST-VET",
    )

    assert event.input_type == "vaccination"
    assert event.payload["animal_id"] == "TEST-COW-100"
    assert event.payload["vaccine"] == "FMD"
