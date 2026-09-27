from dairyos.farm.operations.services.operational_execution_tracking_service import (
    OperationalExecutionTrackingService,
)


class MockTimeline:

    def __init__(self, events=None):
        self.events = events or []

    def get_timeline(self):
        return self.events


class MockStateService:

    def __init__(self, state):
        self.state = state

    def get_state(self):
        return self.state


class ScheduleState:

    def __init__(self):

        self.milking_schedule = []
        self.feeding_schedule = []
        self.health_schedule = []
        self.breeding_schedule = []
        self.task_schedule = []

        self.completed_milking_sessions = []
        self.completed_feeding_sessions = []
        self.completed_health_events = []
        self.completed_breeding_events = []
        self.completed_tasks = []


class FarmState:

    def __init__(self):

        self.schedule_state = ScheduleState()


def test_execution_tracking_detects_completed_activity():

    state = FarmState()

    state.schedule_state.milking_schedule = [
        {
            "shift": "MORNING",
        }
    ]

    timeline = MockTimeline(
        [
            {
                "event_type": "milk_recorded",
                "payload": {
                    "shift": "MORNING",
                },
            }
        ]
    )

    service = OperationalExecutionTrackingService(
        MockStateService(state),
        timeline,
    )

    result = service.evaluate()

    assert result[0]["status"] == (
        "COMPLETED_ON_TIME"
    )


def test_execution_tracking_detects_missing_activity():

    state = FarmState()

    state.schedule_state.feeding_schedule = [
        {
            "feed_type": "TMR",
        }
    ]

    service = OperationalExecutionTrackingService(
        MockStateService(state),
        MockTimeline(),
    )

    result = service.evaluate()

    assert result[0]["status"] == (
        "MISSED"
    )
