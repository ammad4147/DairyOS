from pathlib import Path


ISS = Path(__file__).parents[2] / "tools" / "windows-desktop" / "DairyOS-Installer.iss"
SUPERVISOR = Path(__file__).parents[2] / "src" / "dairyos" / "windows" / "supervisor.py"


def test_uninstaller_does_not_require_preservation_choice():
    source = ISS.read_text(encoding="utf-8-sig")
    assert "Uninstall is application lifecycle only" in source
    assert "MB_YESNOCANCEL" not in source[source.index("function InitializeUninstall(): Boolean;"):]


def test_uninstaller_preservation_uses_verified_data_management_export():
    installer = ISS.read_text(encoding="utf-8-sig")
    supervisor = SUPERVISOR.read_text(encoding="utf-8")
    assert '--farm-data-export' in installer
    assert 'parser.add_argument("--farm-data-export"' in supervisor
    assert "export_farm_data(" in supervisor
    assert "validate_package(result[\"path\"])" in supervisor
    assert '"status": "VERIFIED"' in supervisor


def test_uninstaller_does_not_block_on_preservation():
    source = ISS.read_text(encoding="utf-8-sig")
    initialize = source[source.index("function InitializeUninstall(): Boolean;"):]
    assert "ExportFarmDataForUninstall" not in initialize
    assert "Result := StopInstalledDairyOSForUninstall();" in initialize


def test_clean_installer_still_never_imports_or_discovers_farm_package():
    source = ISS.read_text(encoding="utf-8-sig")
    prepare = source[source.index("function PrepareToInstall"):source.index("function ShouldLaunchDairyOS")]
    assert "CanonicalDairyOSDataRootHasExistingState()" in prepare
    assert "DelTree(CanonicalDairyOSDataRoot(), True, True, True)" in prepare


def test_automation_uninstall_has_no_preservation_wizard_state():
    source = ISS.read_text(encoding="utf-8-sig")
    assert "function UninstallPreservationChoiceFromCommandLine(): String;" in source
    assert "'/PRESERVEFARMDATA=NO'" in source
    assert "function InitializeUninstall(): Boolean;" in source
    assert "WizardSilent" not in source


def test_installer_ci_declares_silent_preservation_decision():
    workflow = (Path(__file__).parents[2] / ".github" / "workflows" / "installer-windows.yml").read_text(encoding="utf-8")
    assert '"/PRESERVEFARMDATA=NO"' in workflow
