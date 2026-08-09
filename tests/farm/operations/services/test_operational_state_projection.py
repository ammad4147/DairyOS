from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.events.farm_operation_event_bus import (
    FarmOperationEventBus,
)

from dairyos.farm.operations.events.operational_state_event_subscriber import (
    OperationalStateEventSubscriber,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.state.operational_state_runtime import (
    OperationalStateRuntime,
)

from dairyos.farm.operations.state.operational_decision_service import (
    OperationalDecisionService,
)



def test_operational_state_updates_from_milk_event():

    service = FarmOperationalStateService()

    subscriber = OperationalStateEventSubscriber(
        service
    )

    event = FarmOperationEvent(

        event_type="milk_recorded",

        animal_id="MILKING-HERD",

        operator="worker",

        payload={
            "shift": "morning",
            "litres": 250,
        },
    )


    subscriber.handle(
        event
    )


    state = service.get_state()


    assert (
        state.milk_status["morning"]["status"]
        ==
        "completed"
    )

    assert (
        state.milk_status["morning"]["litres"]
        ==
        250
    )



def test_operational_state_updates_from_feed_event():

    service = FarmOperationalStateService()

    subscriber = OperationalStateEventSubscriber(
        service
    )


    event = FarmOperationEvent(

        event_type="feed_distributed",

        animal_id=None,

        operator="worker",

        payload={

            "feed_type": "TMR",

            "quantity_kg": 500,

        },

    )


    subscriber.handle(
        event
    )


    state = service.get_state()


    assert (
        state.feeding_status["TMR"]["status"]
        ==
        "completed"
    )


    assert (
        state.feeding_status["TMR"]["quantity_kg"]
        ==
        500
    )



def test_health_event_creates_operational_alert():

    service = FarmOperationalStateService()

    subscriber = OperationalStateEventSubscriber(
        service
    )


    event = FarmOperationEvent(

        event_type="health_observation_recorded",

        animal_id="HF-101",

        operator="worker",

        payload={

            "observation": "Reduced appetite",

            "severity": "high",

        },

    )


    subscriber.handle(
        event
    )


    alerts = (
        service.get_state()
        .health_alerts
    )


    assert len(alerts) == 1

    assert (
        alerts[0]["animal_id"]
        ==
        "HF-101"
    )



def test_operational_decision_service_detects_missing_activity():

    service = FarmOperationalStateService()

    decisions = OperationalDecisionService(
        service
    ).evaluate()


    actions = [
        item["action"]
        for item in decisions
    ]


    assert (
        "record_milk_activity"
        in actions
    )


    assert (
        "record_feed_activity"
        in actions
    )



def test_operational_state_runtime_applies_activity():

    runtime = OperationalStateRuntime()


    runtime.apply_milk_activity(
        shift="evening",
        litres=200,
    )


    summary = runtime.get_summary()


    assert (
        summary["milk_status"]["evening"]["litres"]
        ==
        200
    )
