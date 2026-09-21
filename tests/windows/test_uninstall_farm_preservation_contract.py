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


def test_packaged_preservation_uses_private_appliance_authority():
    supervisor = SUPERVISOR.read_text(encoding="utf-8")
    export_branch = supervisor[supervisor.index('if args.farm_data_export:'):supervisor.index('    if args.lifecycle_install:')]
    assert "if getattr(sys, \"frozen\", False):" in export_branch
    assert "database = prepare_database()" in export_branch
    assert "apply_database_environment(database)" in export_branch
    assert "stage_runtime_database_url()" in export_branch


def test_uninstaller_blocks_if_preservation_fails():
    source = ISS.read_text(encoding="utf-8-sig")
    initialize = source[source.index("function InitializeUninstall(): Boolean;"):]
    assert "ExportFarmDataForUninstall()" in initialize
    assert "Result := False;" in initialize


def test_silent_preservation_success_does_not_block_uninstall():
    source = ISS.read_text(encoding="utf-8-sig")
    start = source.index("function ExportFarmDataForUninstall(): Boolean;")
    end = source.index("function StopInstalledDairyOSForUninstall(): Boolean;", start)
    export = source[start:end]
    assert "SuppressibleMsgBox(" in export
    assert "Complete DairyOS farm data was saved and verified" in export


def test_uninstall_stops_only_bundled_postgres_runtime():
    source = ISS.read_text(encoding="utf-8-sig")
    start = source.index("function StopInstalledDairyOSForUninstall(): Boolean;")
    body = source.index("begin", start)
    end = source.index("function UninstallPreservationChoiceFromCommandLine", body)
    section = source[body:end]
    assert "runtime\\PostgreSQL\\bin\\postgres.exe" in section
    assert "StopInstalledProcessByPath" in section


def test_uninstall_removes_runtime_generated_application_files():
    source = ISS.read_text(encoding="utf-8-sig")
    uninstall_delete = source[source.index("[UninstallDelete]"):source.index("[Code]")]
    assert 'Type: filesandordirs; Name: "{app}"' in uninstall_delete


def test_programdata_deletion_is_bound_to_explicit_remove_choice():
    source = ISS.read_text(encoding="utf-8-sig")
    assert 'Name: "{commonappdata}\\DairyOS"; Check: ShouldDeleteFarmData' in source
    assert "function ShouldDeleteFarmData(): Boolean;" in source
    assert "Result := not PreserveFarmDataOnUninstall;" in source
    assert "PreserveFarmDataOnUninstall := True;" in source


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
    # Silent mode is intentionally used by the refresh/reinstall path so an
    # automated in-place refresh cannot be blocked by the informational dialog.
    # It must not alter the uninstall preservation decision itself.
    prepare = source[source.index("function PrepareToInstall"):source.index("function ShouldLaunchDairyOS")]
    uninstall = source[source.index("function InitializeUninstall(): Boolean;"):]
    assert "WizardSilent" in prepare
    assert "WizardSilent" not in uninstall


def test_installer_ci_declares_silent_preservation_decision():
    workflow = (Path(__file__).parents[2] / ".github" / "workflows" / "installer-windows.yml").read_text(encoding="utf-8")
    assert '"/PRESERVEFARMDATA=NO"' in workflow
