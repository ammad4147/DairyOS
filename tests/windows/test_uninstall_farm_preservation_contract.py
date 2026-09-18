from pathlib import Path


ISS = Path(__file__).parents[2] / "tools" / "windows-desktop" / "DairyOS-Installer.iss"
SUPERVISOR = Path(__file__).parents[2] / "src" / "dairyos" / "windows" / "supervisor.py"


def test_uninstaller_requires_explicit_preservation_choice():
    source = ISS.read_text(encoding="utf-8-sig")
    assert "Do you want to preserve the complete DairyOS farm data before uninstalling?" in source
    assert "MB_YESNOCANCEL" in source
    assert "ChoosePreservationDestination" in source
    assert "ExportFarmDataForUninstall" in source


def test_uninstaller_preservation_uses_verified_data_management_export():
    installer = ISS.read_text(encoding="utf-8-sig")
    supervisor = SUPERVISOR.read_text(encoding="utf-8")
    assert '--farm-data-export' in installer
    assert 'parser.add_argument("--farm-data-export"' in supervisor
    assert "export_farm_data(" in supervisor
    assert "validate_package(result[\"path\"])" in supervisor
    assert '"status": "VERIFIED"' in supervisor


def test_uninstaller_blocks_when_preservation_fails_or_is_cancelled():
    source = ISS.read_text(encoding="utf-8-sig")
    initialize = source[source.index("function InitializeUninstall(): Boolean;"):]
    assert "if Choice = IDCANCEL then" in initialize
    assert "if not ChoosePreservationDestination() then" in initialize
    assert "if not ExportFarmDataForUninstall() then" in initialize
    assert "Result := StopInstalledDairyOSForUninstall();" in initialize


def test_clean_installer_still_never_imports_or_discovers_farm_package():
    source = ISS.read_text(encoding="utf-8-sig")
    prepare = source[source.index("function PrepareToInstall"):source.index("function ShouldLaunchDairyOS")]
    assert "CanonicalDairyOSDataRootHasExistingState()" in prepare
    assert "will not overwrite, import, restore, select, or adopt existing" in prepare
