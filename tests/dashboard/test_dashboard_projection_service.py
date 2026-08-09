from dairyos.dashboard.services.dashboard_projection_service import (
    DashboardProjectionService,
)
from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


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
