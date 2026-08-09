from datetime import datetime, UTC


from dairyos.herd.lifecycle.models.lifecycle_event import (
    LifecycleEvent,
)


from dairyos.farm.herd.services.lifecycle_event_bridge import (
    LifecycleEventBridge,
)


from dairyos.farm.herd.services.animal_event_projection import (
    AnimalEventProjection,
)


from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)



def test_lifecycle_event_bridge_updates_animal_operational_state():

    lifecycle_event = LifecycleEvent(

        animal_id="COW-001",

        previous_status="HEIFER",

        new_status="MILKING_COW",

        location="Main Dairy Shed",

        event_type="lifecycle_transition",

        timestamp=datetime.now(UTC),

    )


    bridge = LifecycleEventBridge()


    farm_event = bridge.convert(
        lifecycle_event
    )


    assert farm_event.event_type == (
        "lifecycle_changed"
    )


    assert farm_event.animal_id == (
        "COW-001"
    )


    repository = (
        AnimalOperationalStateRepository()
    )


    projection = AnimalEventProjection(
        repository=repository
    )


    projection.apply(
        farm_event
    )


    restored = repository.get(
        "COW-001"
    )


    assert restored is not None

    assert restored.lifecycle_status == (
        "MILKING_COW"
    )

    assert restored.previous_lifecycle_status == (
        "HEIFER"
    )

    assert restored.lifecycle_stage == (
        "MILKING_COW"
    )

    assert restored.last_lifecycle_event[
        "event_type"
    ] == "lifecycle_changed"

    assert restored.last_lifecycle_event[
        "source_event_type"
    ] == "lifecycle_transition"
