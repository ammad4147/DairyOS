from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def text(path):return (ROOT/path).read_text(encoding="utf-8")
def test_health_contract():
 v=text("src/DairyOS.Web/src/components/HealthTab.tsx")
 assert "/farm/finance-ledger" not in v
 assert "Vet Expenses" not in v
 assert "Clinical Health" in v
 assert "Complete Clinical Log" in v
 assert "Mark Healthy" in v
 assert "Declare Healthy" not in v
 assert "Symptoms & Details" in v
 assert "Next Check-up" in v
 assert "/farm/treatments" in v
 assert "/vaccinations" not in v
 assert "/resolve" in v

def test_settings_contract():
 v=text("src/DairyOS.Web/src/components/SettingsTab.tsx");assert "STANDARDS" not in v;assert "smtp.gmail.com" in v;assert "smtp-mail.outlook.com" in v;assert "smtp.mail.yahoo.com" in v;assert "Notification Recipients" in v;assert "System Date & Time" in v;assert "Navigation Visibility" in v

def test_hidden_navigation_tabs_only_filter_header_buttons():
 v=text("src/DairyOS.Web/src/App.tsx")
 settings=text("src/DairyOS.Web/src/components/SettingsTab.tsx")
 assert "visibleNavItems=navItems.filter" in v
 assert "hiddenNavigationTabs.includes(tab.id)" in v
 assert settings.count("onHiddenNavigationTabsChange?.(hidden)") == 1
 for view in ("dashboard", "animals", "milk", "feed", "finance", "breeding", "health", "vaccination", "cop"):
  assert f"currentView==='{view}'" in v
def test_passport_final_disposal():
 v=text("src/DairyOS.Web/src/components/AnimalPassportModal.tsx");assert "Final Disposal" in v;assert "Record Mortality" in v;assert "['exit','Sold / Mortality']" not in v;assert "disposition:'DECEASED'" in v
def test_finance_animal_sale_linkage():
 v=text("src/DairyOS.Web/src/components/FinanceTab.tsx")
 for label in ("Milking Animal Sale","Dry Animal Sale","Heifer Sale","Female Calf Sale","Male Calf Sale","Bull Sale"):assert label in v
 assert "Select Animal ID being sold" in v and "/disposition" in v and "status:'VOID'" in v
def test_milk_operator_alert_preserved():
 v=text("src/DairyOS.Web/src/components/MilkTab.tsx");assert "TODAY'S MILKING SESSIONS ALREADY RECORDED" in v;assert "MILKING_SESSION_ALREADY_RECORDED" in v

def test_animal_identity_labels_preserve_permanent_and_legacy_distinction():
 v=text("src/DairyOS.Web/src/components/AnimalPassportModal.tsx")
 assert "Permanent DairyOS Animal ID" in v
 assert "Legacy ID (optional)" in v
 assert "does not replace the permanent DairyOS ID" in v

def test_global_navigation_fits_without_horizontal_scrolling():
 v=text("src/DairyOS.Web/src/App.tsx")
 assert "margin:'0 4px',overflowX:'hidden',overflowY:'hidden'" in v
 assert "gap:3,flex:'0 0 auto'" in v
 assert "padding:'5px',borderRadius:6,cursor:'pointer',fontSize:9" in v

def test_header_icon_controls_have_accessible_names():
 v=text("src/DairyOS.Web/src/App.tsx")
 passport=text("src/DairyOS.Web/src/components/AnimalPassportModal.tsx")
 assert "aria-label={`Active warnings (${activeCount})`}" in v
 assert 'aria-label="System Settings"' in v
 assert 'aria-label="Close Animal Passport"' in passport

def test_passport_renderer_preserves_permanent_identifier_casing():
 v=text("src/DairyOS.Web/src/components/OperatorDataBlock.tsx")
 assert "IDENTIFIER_KEYS" in v
 assert "return <span>{String(value)}</span>;" in v
