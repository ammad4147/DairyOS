from datetime import datetime, UTC

from dairyos.application.dashboard.integrations.event_dashboard_adapter import (
    EventDashboardAdapter,
)


class FakeEvent:

    event_type = "milk_recorded"

    operator = "Ahmed"

    timestamp = datetime.now(UTC)

    payload = {
        "description": "Morning milking completed"
    }



class FakeRepository:


    def get_all(self):

        return [
            FakeEvent()
        ]



def test_event_adapter_converts_operational_event():

    adapter = EventDashboardAdapter(
        FakeRepository()
    )


    activities = (
        adapter.get_activities()
    )


    assert len(activities) == 1

    assert (
        activities[0].event_type
        == "milk_recorded"
    )

    assert (
        activities[0].source
        == "Ahmed"
    )
