import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "DairyOS.Web" / "src" / "App.tsx"
NAVIGATION = ROOT / "src" / "DairyOS.Web" / "src" / "navigation.ts"
SETTINGS = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "SettingsTab.tsx"
ANALYTICS = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "Analytics.tsx"
DIGITAL_TWIN_PANEL = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "DigitalTwinPanel.tsx"
DIGITAL_TWIN_API = ROOT / "src" / "dairyos" / "api" / "digital_twin"
DIGITAL_TWIN_PLATFORM = ROOT / "src" / "dairyos" / "platform" / "digital_twin"


def test_operator_shell_has_exactly_nine_navigation_tabs_and_one_dashboard_surface():
    text = APP.read_text(encoding="utf-8-sig")
    navigation = NAVIGATION.read_text(encoding="utf-8-sig")
    labels = ["Dashboard", "Animals", "Milk", "Feed", "Finance", "Breeding", "Health", "Vaccination", "COP"]
    assert len(labels) == 9
    assert re.findall(r"label:\s*'([^']+)'", navigation) == labels
    assert "label: 'COML'" not in navigation
    assert "label: 'Analytics'" not in navigation
    assert "NAVIGATION_TABS.map" in text
    assert "UnifiedDashboard" in text
    assert "MainDashboard" not in text


def test_analytics_surface_is_retired_from_operator_shell():
    text = APP.read_text(encoding="utf-8-sig")
    assert "./components/Analytics" not in text
    assert "currentView==='analytics'" not in text
    assert not ANALYTICS.exists()
    assert not DIGITAL_TWIN_PANEL.exists()
    assert not DIGITAL_TWIN_API.exists()
    assert not DIGITAL_TWIN_PLATFORM.exists()
    assert "currentView==='cop'" in text
    assert "currentView==='cop'&&<COML/>" in text
    assert "COPOfficializationPanel" not in text
    assert "DigitalTwinPanel" not in text


def test_settings_has_no_operator_facing_deployment_surface():
    text = SETTINGS.read_text(encoding="utf-8-sig")
    assert "DEPLOYMENT" not in text
    assert "Deployment" not in text
    assert "deployment/activate" not in text


def test_frontend_does_not_define_a_second_animal_classification_service():
    text = APP.read_text(encoding="utf-8-sig")
    assert "AnimalClassificationService" not in text
    assert "function categoryFromAnimal" not in text
    assert "animal.animal_category" in text
