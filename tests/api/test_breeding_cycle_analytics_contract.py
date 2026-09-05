from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = (ROOT / "src/dairyos/api/reproduction_management.py").read_text(encoding="utf-8")
UI = (ROOT / "src/DairyOS.Web/src/components/BreedingTab.tsx").read_text(encoding="utf-8")


def test_reproduction_api_exposes_cycle_and_analytics_projections():
    assert '@router.get("/cycles")' in API
    assert '@router.get("/analytics")' in API
    assert '"cycles": cycles' in API
    assert '"current_cycle":' in API


def test_breeding_ui_consumes_cycle_authority_not_lifetime_last_matching_events():
    assert "getJson<any>('/farm/reproduction/cycles')" in UI
    assert "getJson<Analytics>('/farm/reproduction/analytics')" in UI
    assert "const activeCycle" in UI
    assert "const cycleEvents = activeCycle?.events || [];" in UI
    assert "Breeding Analytics — Cycle Linked" in UI
    assert "AI / Sire Performance" in UI
    assert "Animal Reproductive Performance" in UI
    assert "Evidence cycles:" in UI
    assert "Service Attempt Performance" in UI
