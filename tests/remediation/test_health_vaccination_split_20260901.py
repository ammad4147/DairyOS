from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def text(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_top_level_navigation_and_routes_are_split():
    s = text("src/DairyOS.Web/src/App.tsx")
    navigation = text("src/DairyOS.Web/src/navigation.ts")
    assert "label: 'Health'" in navigation
    assert "label: 'Vaccination'" in navigation
    assert "currentView==='health'" in s
    assert "currentView==='vaccination'" in s
    assert "VaccinationTab" in s
    assert "vaccination:'#15803d'" in s
    assert "'vaccination'" in s


def test_health_is_clinical_only():
    s = text("src/DairyOS.Web/src/components/HealthTab.tsx")
    assert "Clinical Health" in s
    assert "Complete Clinical Log" in s
    assert "Record Treatment" in s
    assert "Mark Healthy" in s
    assert "Symptoms & Details" in s
    assert "Next Check-up" in s
    assert "/farm/treatments" in s
    assert "/farm/health-cases" in s
    assert "/vaccinations" not in s
    assert "VACCINES=" not in s


def test_vaccination_is_preventive_only():
    s = text("src/DairyOS.Web/src/components/VaccinationTab.tsx")
    assert "Record Vaccination Given" in s
    assert "Mark Vaccination GIVEN" in s
    assert "Action Queue - earliest due first" in s
    assert "Overdue Vaccinations" in s
    assert "Due Next 30 Days" in s
    assert "Animals With No Vax History" in s
    assert "/vaccinations" in s
    assert "/farm/treatments" not in s
    assert "/farm/health-cases" not in s


def test_dashboard_has_distinct_health_and_vaccination_routes():
    s = text("src/DairyOS.Web/src/components/UnifiedDashboard.tsx")
    assert "Clinical Health" in s
    assert "Vaccination Operations" in s
    assert "onNavigate?.('health')" in s
    assert "onNavigate?.('vaccination')" in s


def test_passport_has_distinct_health_and_vaccination_views():
    s = text("src/DairyOS.Web/src/components/AnimalPassportModal.tsx")
    assert "['health','Clinical Health']" in s
    assert "['vaccination','Vaccination']" in s
    assert "tab==='health'" in s
    assert "tab==='vaccination'" in s
    assert "Clinical History" in s
    assert "Treatment History" in s
    assert "Vaccination History" in s
    assert "passport?.history?.health" in s
    assert "passport?.history?.treatments" in s
    assert "passportVaccinations" in s
    assert "/health`)" not in s
    assert "/treatments`)" not in s
    assert "/vaccinations`)" in s


def test_backend_exposes_separate_summary_surfaces():
    s = text("src/dairyos/api/health.py")
    assert '@router.get("/farm/health/summary")' in s
    assert '@router.get("/farm/vaccination/summary")' in s
    assert '"activeSickAnimals"' in s
    assert '"vaccinationsOverdue"' in s
    assert '"animalsWithNoVaccinationHistory"' in s


def test_dashboard_backend_preserves_compatibility_and_separate_vaccination_projection():
    s = text("src/dairyos/api/dashboard.py")
    assert 'payload["health"]' in s
    assert 'payload["vaccination"]' in s
    assert '"completed_vaccinations"' in s
    assert '"due_vaccinations"' in s
