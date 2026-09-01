from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def text(p): return (ROOT/p).read_text(encoding="utf-8-sig")
def test_health_ui_contract():
    s=text("src/DairyOS.Web/src/components/HealthTab.tsx")
    assert "Dr. Tariq Mahmood" not in s
    assert "Vaccinations Due / Overdue" in s
    assert "Record Vaccination Given" in s
    assert "Mark Vaccination Given" in s
    assert "Most Recorded Illnesses / Diagnoses" in s
    assert "Search animal, illness, medicine, vet" in s
    assert "declareHealthy(c)" in s
def test_health_dashboard_refresh():
    assert "onChanged={()=>setDashboardRefreshVersion(prev=>prev+1)}" in text("src/DairyOS.Web/src/App.tsx")
def test_passport_health_join():
    s=text("src/DairyOS.Web/src/components/AnimalPassportModal.tsx")
    assert "passportHealth" in s and "/treatments`)" in s and "/vaccinations`)" in s
def test_health_summary_live():
    s=text("src/dairyos/api/health.py")
    assert "TODO: Replace with real aggregation" not in s
    assert "LIVE_PERSISTED_DATA" in s
