from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

def text(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")

def test_breeding_ui_has_no_heat_or_estrus_operational_concept():
    s = text("src/DairyOS.Web/src/components/BreedingTab.tsx")
    for token in ["Standing Heat","Heat Observation","Active Heat Standing","On Heat","HEAT_OBSERVED","heat_detected","heat_detection","estrus","oestrus","last_heat"]:
        assert token not in s
    assert "Manual AI Candidates" in s
    assert "Manual AI authority" in s
    assert "operator entry remains authoritative" in s
    assert "days after calving" in s
    assert "Insemination Success Analytics" in s
    assert "1st Attempt" in s and "2nd Attempt" in s and "3rd Attempt" in s

def test_dashboard_reproduction_is_exactly_three_operational_metrics():
    ui = text("src/DairyOS.Web/src/components/UnifiedDashboard.tsx")
    client = text("src/DairyOS.Web/src/api/commandDashboardClient.ts")
    backend = text("src/dairyos/api/dashboard.py")
    assert "Pregnancy Ratio" in ui
    assert "reproData.pregnancyRatio" in ui
    assert "repeat(3,minmax(0,1fr))" in ui
    assert "On Heat" not in ui
    assert "onHeat" not in client
    assert "pregnancyRatio" in client
    assert '"onHeat"' not in backend
    assert '"on_heat"' not in backend
    assert '"pregnancy_ratio_percent"' in backend

def test_reproductive_core_has_no_heat_linkage():
    files = [
        "src/dairyos/herd/reproduction/services/reproductive_event_classifier.py",
        "src/dairyos/farm/reproduction/services/reproductive_state_service.py",
        "src/dairyos/api/farm_planning.py",
        "src/dairyos/api/reproduction_management.py",
        "src/dairyos/application/animal_passport.py",
    ]
    banned = ["HEAT_DETECTION_EVENTS","is_heat_detection","HEAT_OBSERVED","HEAT_DETECTED","last_heat","heat_detections"]
    for path in files:
        s = text(path)
        for token in banned:
            assert token not in s, f"{token} remained in {path}"

def test_heat_reentry_is_rejected_at_breeding_write_boundary():
    s = text("src/dairyos/api/farm_data_entry.py")
    assert "retired_heat_events" in s
    assert '"heat_detected"' in s
    assert '"estrus"' in s
    assert "Heat/estrus breeding events have been retired from DairyOS" in s

def test_attempt_success_resets_after_calving_and_uses_documented_outcomes():
    from dairyos.api.reproduction_management import _insemination_attempt_success
    def row(record_id, animal, event_type, day, result=None):
        return SimpleNamespace(record_id=record_id, animal_id=animal, event_type=event_type, timestamp=datetime(2026,1,day,tzinfo=timezone.utc), result=result, technician=None)
    records = [
        row("a1","A","insemination",1),
        row("a1p","A","pregnancy_negative",2,"NEGATIVE"),
        row("a2","A","insemination",3),
        row("a2p","A","pregnancy_confirmed",4,"POSITIVE"),
        row("ac","A","calving",5),
        row("a3","A","insemination",6),
        row("a3p","A","pregnancy_confirmed",7,"POSITIVE"),
    ]
    metrics = _insemination_attempt_success(records)
    assert metrics["1"]["services_with_documented_outcome"] == 2
    assert metrics["1"]["confirmed_pregnancies"] == 1
    assert metrics["1"]["success_ratio_percent"] == 50.0
    assert metrics["2"]["services_with_documented_outcome"] == 1
    assert metrics["2"]["confirmed_pregnancies"] == 1
    assert metrics["2"]["success_ratio_percent"] == 100.0
    assert metrics["3"]["success_ratio_percent"] is None

def test_heat_and_estrus_reentry_is_rejected_by_api(client, registered_animal):
    for event_type in (
        "heat",
        "heat_detected",
        "heat_detection",
        "oestrus",
        "estrus",
    ):
        response = client.post(
            "/farm/breeding",
            json={
                "animal_id": registered_animal,
                "event_type": event_type,
                "result": "detected",
                "operator": "TEST",
            },
        )
        assert response.status_code == 422
        assert "retired from DairyOS" in response.text

def test_retired_heat_model_cannot_reappear_in_production_source():
    allowed = {
        "src/dairyos/api/farm_data_entry.py",
    }
    banned = (
        "HEAT_OBSERVED",
        "HEAT_DETECTED",
        "Standing Heat",
        "Heat Observation",
        "Active Heat Standing",
        "On Heat",
        "last_heat_date",
        "last_heat",
        "is_heat_detection",
        "heat_detections",
        "HEAT_DETECTION_EVENTS",
        "HeatEvent",
        "record_heat(",
        "save_heat(",
        "get_heat(",
        "heat_detected",
        "heat_detection",
        "lifetime_heat",
        "oestrus",
        "estrus",
    )

    hits = []
    for source_root in (
        ROOT / "src/dairyos",
        ROOT / "src/DairyOS.Web/src",
    ):
        for path in source_root.rglob("*"):
            if (
                not path.is_file()
                or path.suffix not in {".py", ".ts", ".tsx", ".js"}
            ):
                continue
            relative = path.relative_to(ROOT).as_posix()
            if (
                relative in allowed
                or "heat_stress" in relative.lower()
            ):
                continue
            source = path.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )
            source = source.replace(
                "record_heat_stress(",
                "ENVIRONMENTAL_HEAT_STRESS_RECORD(",
            ).replace(
                "heat_stress_status(",
                "ENVIRONMENTAL_HEAT_STRESS_STATUS(",
            )
            for token in banned:
                if token in source:
                    hits.append(f"{relative}: {token}")

    assert hits == []

def test_legacy_heat_model_file_is_deleted():
    assert not (
        ROOT / "src/dairyos/farm/reproduction/models/heat_event.py"
    ).exists()


def test_displayed_gestation_uses_insemination_and_operational_date_everywhere():
    source = text("src/DairyOS.Web/src/components/BreedingTab.tsx")

    assert "as_of_date?: string" in source
    assert "daysBetween(aiDate, asOfDate)" in source
    assert "Date.now()" not in source
    assert ".map(s => s.pregnancy_confirmed_date)" not in source


def test_breeding_date_only_arithmetic_is_timezone_stable():
    source = text("src/DairyOS.Web/src/components/BreedingTab.tsx")

    assert "Date.UTC(year, month - 1, day)" in source
    assert "d.setDate(d.getDate() + n)" not in source
    assert "new Date(`${v}T00:00:00`)" not in source

def test_breeding_mutations_refresh_shell_herd_dashboard_and_alerts():
    breeding = text("src/DairyOS.Web/src/components/BreedingTab.tsx")
    app = text("src/DairyOS.Web/src/App.tsx")

    assert "onChanged?: () => void | Promise<void>" in breeding
    assert "await onChanged?.();" in breeding
    assert (
        "onChanged={async()=>{await refreshAnimals();"
        "setDashboardRefreshVersion(prev=>prev+1);"
        "await refreshAlerts()}}"
    ) in app
