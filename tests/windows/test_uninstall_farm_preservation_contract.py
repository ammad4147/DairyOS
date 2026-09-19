from pathlib import Path


ISS = Path(__file__).parents[2] / "tools" / "windows-desktop" / "DairyOS-Installer.iss"
SUPERVISOR = Path(__file__).parents[2] / "src" / "dairyos" / "windows" / "supervisor.py"


def test_uninstaller_requires_preservation_choice_for_interactive_uninstall():
    source = ISS.read_text(encoding="utf-8-sig")
    initialize = source[source.index("function InitializeUninstall(): Boolean;"):]
    assert "MB_YESNOCANCEL" in initialize


def test_uninstaller_preservation_uses_verified_data_management_export():
    installer = ISS.read_text(encoding="utf-8-sig")
    supervisor = SUPERVISOR.read_text(encoding="utf-8")
    assert '--farm-data-export' in installer
    assert 'parser.add_argument("--farm-data-export"' in supervisor
    assert "export_farm_data(" in supervisor
    assert "validate_package(result[\"path\"])" in supervisor
    assert '"status": "VERIFIED"' in supervisor


def test_uninstaller_blocks_if_preservation_fails():
    source = ISS.read_text(encoding="utf-8-sig")
    initialize = source[source.index("function InitializeUninstall(): Boolean;"):]
    assert "ExportFarmDataForUninstall()" in initialize
    assert "Result := False;" in initialize


def test_clean_installer_still_never_imports_or_discovers_farm_package():
    source = ISS.read_text(encoding="utf-8-sig")
    prepare = source[source.index("function PrepareToInstall"):source.index("function ShouldLaunchDairyOS")]
    assert "CanonicalDairyOSDataRootHasExistingState()" in prepare
    assert "DelTree(CanonicalDairyOSDataRoot(), True, True, True)" not in prepare


def test_automation_uninstall_has_no_preservation_wizard_state():
    source = ISS.read_text(encoding="utf-8-sig")
    assert "function UninstallPreservationChoiceFromCommandLine(): String;" in source
    assert "'/PRESERVEFARMDATA=NO'" in source
    assert "function InitializeUninstall(): Boolean;" in source
    assert "WizardSilent" not in source


def test_installer_ci_declares_silent_preservation_decision():
    workflow = (Path(__file__).parents[2] / ".github" / "workflows" / "installer-windows.yml").read_text(encoding="utf-8")
    assert '"/PRESERVEFARMDATA=NO"' in workflow
