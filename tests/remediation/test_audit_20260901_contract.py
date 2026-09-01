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
 v=text("src/DairyOS.Web/src/components/SettingsTab.tsx");assert "STANDARDS" not in v;assert "smtp.gmail.com" in v;assert "smtp-mail.outlook.com" in v;assert "smtp.mail.yahoo.com" in v;assert "Notification Recipients" in v;assert "System Date & Time" in v
def test_passport_final_disposal():
 v=text("src/DairyOS.Web/src/components/AnimalPassportModal.tsx");assert "Final Disposal" in v;assert "Record Mortality" in v;assert "['exit','Sold / Mortality']" not in v;assert "disposition:'DECEASED'" in v
def test_finance_animal_sale_linkage():
 v=text("src/DairyOS.Web/src/components/FinanceTab.tsx")
 for label in ("Milking Animal Sale","Dry Animal Sale","Heifer Sale","Female Calf Sale","Male Calf Sale","Bull Sale"):assert label in v
 assert "Select Animal ID being sold" in v and "/disposition" in v and "status:'VOID'" in v
def test_milk_operator_alert_preserved():
 v=text("src/DairyOS.Web/src/components/MilkTab.tsx");assert "TODAY'S MILKING SESSIONS ALREADY RECORDED" in v;assert "MILKING_SESSION_ALREADY_RECORDED" in v
