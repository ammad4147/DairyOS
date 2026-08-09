from dairyos.farm.operations.runtime.farm_operations_runtime import (
    FarmOperationsRuntime,
)


def test_operational_activity_lifecycle_publishes_events():

    runtime = FarmOperationsRuntime()


    activity = runtime.create_activity(
        "MILKING",
        {
            "shift": "MORNING",
        },
    )


    runtime.assign_activity(
        activity.activity_id,
        "Farm Worker",
    )


    runtime.start_activity(
        activity.activity_id,
    )


    runtime.complete_activity(
        activity.activity_id,
    )


    runtime.verify_activity(
        activity.activity_id,
    )


    assert activity.status == "VERIFIED"


    event_types = [
        event.event_type
        for event in runtime.events
    ]


    assert "activity_assigned" in event_types

    assert "activity_started" in event_types

    assert "activity_completed" in event_types

    assert "activity_verified" in event_types