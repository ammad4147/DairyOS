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


def test_vaccination_is_schedule_first_and_preventive_only():
    source = text("src/DairyOS.Web/src/components/VaccinationTab.tsx")

    assert "Add Vaccination Schedule" in source
    assert "Mark Given" in source
    assert "Overall Log" in source
    assert "treatment" not in source.lower()

def test_dashboard_has_distinct_health_and_vaccination_routes():
    source = text("src/DairyOS.Web/src/components/UnifiedDashboard.tsx")

    assert "Health" in source
    assert "Vaccination" in source
    assert "health" in source.lower()
    assert "vaccination" in source.lower()

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


def test_dashboard_backend_preserves_compatibility_and_vaccination_projection():
    s = text("src/dairyos/api/dashboard.py")
    assert 'payload["health"]' in s
    assert 'payload["vaccination"]' in s
    assert '"sick_animals"' in s
    assert '"due_animals"' in s
    assert '"completed_vaccinations"' in s
    assert '"due_vaccinations"' in s


def test_dashboard_cards_show_current_attention_lists_not_lifetime_totals():
    s = text("src/DairyOS.Web/src/components/UnifiedDashboard.tsx")
    client = text("src/DairyOS.Web/src/api/commandDashboardClient.ts")
    assert "sickAnimals" in client
    assert "dueAnimals" in client
    assert "No active sick animals" in s
    assert "No vaccinations due today" in s
    assert "DUE TODAY" in s
    assert "OVERDUE" in s
    assert "vaccinationsDueToday" in s
    assert "overdueVaccinations" in s
    assert "onNavigate?.('health')" in s
    assert "onNavigate?.('vaccination')" in s
    assert "healthData.completedVax" not in s
    assert "healthData.dueVax" not in s
    assert "role=\"button\"" in s
