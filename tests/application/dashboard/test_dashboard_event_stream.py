from dairyos.application.dashboard.integrations.event_dashboard_adapter import (
    EventDashboardAdapter,
)

from dairyos.data.repositories.operational_event_repository import (
    OperationalEventRepository,
)

from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)



def test_dashboard_reads_operational_event_stream():

    repository = OperationalEventRepository()


    event = FarmOperationEvent(

        event_type="milk_recorded",

        animal_id="MILKING_HERD",

        operator="Ahmed",

        payload={
            "description": "Morning milking completed",
            "litres": 250,
        },
    )


    repository.add(event)


    adapter = EventDashboardAdapter(
        event_repository=repository
    )


    activities = adapter.get_activities()


    assert len(activities) == 1

    assert (
        activities[0].event_type
        ==
        "milk_recorded"
    )

    assert (
        activities[0].source
        ==
        "Ahmed"
    )

    assert (
        activities[0].description
        ==
        "Morning milking completed"
    )
