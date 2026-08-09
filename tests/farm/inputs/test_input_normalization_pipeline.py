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
