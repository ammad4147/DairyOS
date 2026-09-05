from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BREEDING = (ROOT / "src/DairyOS.Web/src/components/BreedingTab.tsx").read_text(encoding="utf-8")
FINANCE = (ROOT / "src/DairyOS.Web/src/components/FinanceTab.tsx").read_text(encoding="utf-8")
MILK = (ROOT / "src/DairyOS.Web/src/components/MilkTab.tsx").read_text(encoding="utf-8")
PASSPORT = (ROOT / "src/DairyOS.Web/src/components/AnimalPassportModal.tsx").read_text(encoding="utf-8")
FARM_DATE = (ROOT / "src/DairyOS.Web/src/utils/farmDate.ts").read_text(encoding="utf-8")
DASHBOARD = (ROOT / "src/DairyOS.Web/src/api/commandDashboardClient.ts").read_text(encoding="utf-8")


def test_farm_date_helper_uses_pakistan_timezone_and_preserves_operator_override():
    assert "timeZone: 'Asia/Karachi'" in FARM_DATE
    assert "current === previousAutomatic ? next : current" in FARM_DATE


def test_breeding_event_date_is_farm_local_and_resets_when_form_opens():
    assert "useFarmDateField" in BREEDING
    assert "resetFormDateToToday(); setShowEventModal(true)" in BREEDING
    assert "new Date().toISOString().split('T')[0]" not in BREEDING
    assert 'value={formDate} onChange={e => setFormDate(e.target.value)}' in BREEDING


def test_other_operational_entry_dates_use_rolling_farm_date_defaults():
    assert "useFarmDateField" in FINANCE
    assert "resetExpenseDateToToday()" in FINANCE
    assert "resetRevDateToToday()" in FINANCE
    assert "useFarmDateField" in MILK
    assert "useFarmDateField" in PASSPORT
    assert "resetExitEffectiveDateToToday()" in PASSPORT


def test_semantic_dates_remain_operator_selected_not_forced_to_today():
    assert 'label="Date of Birth"' in PASSPORT
    assert 'value={form.birthDate}' in PASSPORT
    assert 'label="Date of Acquisition"' in PASSPORT
    assert 'value={form.acquisitionDate}' in PASSPORT


def test_dashboard_fallback_date_uses_farm_local_today():
    assert "todayDate: farmToday()" in DASHBOARD
    assert 'todayDate: new Date().toISOString().split("T")[0]' not in DASHBOARD
