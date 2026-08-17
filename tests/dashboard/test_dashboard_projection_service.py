from dairyos.dashboard.services.dashboard_projection_service import (
    DashboardProjectionService,
)
from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class _Journal:
    def count(self):
        return 0

    def latest(self):
        return []


def test_dashboard_projection_populates_live_milk_widgets():
    state = FarmOperationalState(
        farm_id="trident",
        operational_date="2026-08-07",
    )
    state.record_milk_activity(
        shift="morning",
        litres=125,
        operator="Amina",
        animal_id="COW-001",
    )

    dashboard = DashboardProjectionService().project(farm_state=state)
    milk_zone = next(
        zone
        for zone in dashboard.layout.zones
        if zone.zone_id == "milk"
    )

    assert {
        widget.widget_id: widget.value
        for widget in milk_zone.widgets
    } == {
        "milk.today": 125,
        "milk.shift": "morning",
        "milk.operator": "Amina",
    }


def test_dashboard_projection_populates_live_herd_widgets():
    state = FarmOperationalState(
        farm_id="trident",
        operational_date="2026-08-07",
    )
    state.record_animal("COW-001", {"status": "milking"})
    state.record_animal("COW-002", {"status": "dry"})
    state.add_health_alert("COW-001", "Reduced appetite", "warning")

    dashboard = DashboardProjectionService().project(farm_state=state)
    herd_zone = next(
        zone
        for zone in dashboard.layout.zones
        if zone.zone_id == "herd"
    )

    assert {
        widget.widget_id: widget.value
        for widget in herd_zone.widgets
    } == {
        "herd.summary": 2,
        "herd.lactating": 1,
        "herd.attention": 1,
    }


def test_compatibility_dashboard_exposes_authoritative_kpi_fields():
    state = FarmOperationalState(
        farm_id="trident",
        operational_date="2026-08-17",
    )
    state.record_animal("COW-001", {"status": "milking"})
    state.record_animal("COW-002", {"status": "dry"})
    state.record_milk_activity(
        shift="morning",
        litres=125,
        operator="Amina",
        animal_id="COW-001",
    )
    state.add_health_alert(
        "COW-001",
        "Reduced appetite",
        "warning",
    )

    service = DashboardProjectionService()
    dashboard = service.project_compatibility_dashboard(
        farm_state=state,
        event_journal=_Journal(),
        milk_read_model={
            "total_litres": 125,
            "group_yield": {
                "shift_production": {
                    "MORNING": 125,
                    "AFTERNOON": None,
                    "EVENING": None,
                },
            },
            "production_trend": {
                "prior_date": "2026-08-16",
                "prior_total_litres": 132,
                "variance_percentage": -5.3,
                "comparison_status": "COMPARED",
            },
        },
    )

    assert dashboard["animals"]["milking_percentage"] == 50.0
    assert dashboard["milk"]["production_date"] == "2026-08-17"
    assert dashboard["milk"]["litres"] == 125
    assert dashboard["milk"]["previous_production_date"] == "2026-08-16"
    assert dashboard["milk"]["previous_litres"] == 132
    assert dashboard["milk"]["change_percent"] == -5.3
    assert dashboard["milk"]["morning_litres"] == 125
    assert dashboard["health"]["status"] == "AMBER"
    assert dashboard["health"]["active_exceptions"] == 1
    assert dashboard["health"]["critical_cases"] == 0


def test_health_read_model_turns_critical_alerts_red():
    state = FarmOperationalState(
        farm_id="trident",
        operational_date="2026-08-17",
    )
    state.record_animal("COW-001", {"status": "milking"})
    state.add_health_alert(
        "COW-001",
        "Critical temperature",
        "critical",
    )

    dashboard = DashboardProjectionService().project_compatibility_dashboard(
        farm_state=state,
        event_journal=_Journal(),
    )

    assert dashboard["health"] == {
        "status": "RED",
        "active_exceptions": 1,
        "critical_cases": 1,
    }
