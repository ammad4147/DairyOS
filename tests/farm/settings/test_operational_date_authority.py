from datetime import date

from dairyos.api.farm_data_entry import next_milking_session
from dairyos.farm.command_center.services.missing_input_detection_service import (
    MissingInputDetectionService,
)
from dairyos.farm.day.runtime.farm_day_runtime import FarmDayRuntime
from dairyos.farm.operations.state.operational_decision_service import (
    OperationalDecisionService,
)
from dairyos.farm.operations.state.operational_state_runtime import (
    OperationalStateRuntime,
)


class FakeAuthority:
    def __init__(self, operational_date="2030-04-15"):
        self.operational_date = operational_date

    def current_date_string(self):
        return self.operational_date

    def current_date(self):
        return date.fromisoformat(
            self.operational_date
        )


class FakeOperationalStateService:
    def __init__(self, state):
        self.state = state

    def get_state(self):
        return self.state


def test_farm_day_runtime_uses_injected_operational_date_authority():
    runtime = FarmDayRuntime(
        operational_date_authority=FakeAuthority(
            "2030-04-15"
        )
    )

    day = runtime.start_day()

    assert day.operational_date == "2030-04-15"


def test_operational_state_runtime_uses_injected_operational_date_authority():
    runtime = OperationalStateRuntime(
        operational_date_authority=FakeAuthority(
            "2030-04-15"
        )
    )

    state = runtime.initialize()

    assert state.operational_date == "2030-04-15"


def test_missing_input_detection_compares_against_authoritative_date():
    state = type(
        "State",
        (),
        {
            "operational_date": "2030-04-15",
            "milk_production_summary": {
                "milking_events_count": 1,
            },
            "feeding_status": {
                "feeding_events": 1,
            },
            "workforce_status": {
                "staff_present": 1,
            },
        },
    )()

    service = MissingInputDetectionService(
        operational_date_authority=FakeAuthority(
            "2030-04-15"
        )
    )

    assert service.detect(state) == []


def test_missing_input_detection_does_not_use_machine_today():
    state = type(
        "State",
        (),
        {
            "operational_date": "2030-04-15",
            "milk_production_summary": {
                "milking_events_count": 1,
            },
            "feeding_status": {
                "feeding_events": 1,
            },
            "workforce_status": {
                "staff_present": 1,
            },
        },
    )()

    service = MissingInputDetectionService(
        operational_date_authority=FakeAuthority(
            "2030-04-15"
        )
    )

    assert service.detect(state) == []


def test_operational_decision_service_uses_authoritative_date():
    state = type(
        "State",
        (),
        {
            "operational_date": "2030-04-15",
            "milk_production_summary": {
                "milking_events_count": 1,
            },
            "feeding_status": {
                "feeding_events": 1,
            },
            "workforce_status": {
                "staff_present": 1,
            },
            "health_state": {},
            "health_alerts": [],
            "exceptions": [],
            "open_tasks": [],
            "schedule_state": None,
        },
    )()

    class Intelligence:
        def evaluate(self, state):
            return []

    service = OperationalDecisionService(
        FakeOperationalStateService(state),
        workforce_intelligence_service=Intelligence(),
        inventory_intelligence_service=Intelligence(),
        equipment_intelligence_service=Intelligence(),
        financial_intelligence_service=Intelligence(),
        operational_date_authority=FakeAuthority(
            "2030-04-15"
        ),
    )

    assert service._missing_input_decisions(state) == []
