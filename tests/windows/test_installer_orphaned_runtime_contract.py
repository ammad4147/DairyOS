from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"


def test_installer_provisions_pg_ctl_in_application_owned_recovery_folder():
    source = INSTALLER.read_text(encoding="utf-8")
    recovery_root = "{commonappdata}\\DairyOS-Recovery\\PostgreSQL\\bin"
    for filename in (
        "pg_ctl.exe",
        "libpq.dll",
        "libintl-9.dll",
        "libiconv-2.dll",
        "libssl-3-x64.dll",
        "libcrypto-3-x64.dll",
        "libwinpthread-1.dll",
        "zlib1.dll",
    ):
        assert f'DestDir: "{recovery_root}"' in source
        assert f'\\bin\\{filename}"; DestDir: "{recovery_root}"' in source
    build = (ROOT / "scripts" / "Build-DairyOS-Installer.ps1").read_text(encoding="utf-8-sig")
    assert '"/DBundlePath=" + $bundlePath' in build
    recovery = source[source.index("function StopInstalledDairyOSForUninstall(): Boolean;"):]
    assert "ExtractTemporaryFile" not in recovery
    assert "{commonappdata}\\DairyOS-Recovery\\PostgreSQL\\bin\\pg_ctl.exe" in recovery


def test_recovery_tools_never_live_inside_the_farm_data_root():
    source = INSTALLER.read_text(encoding="utf-8")
    assert "Result := ExpandConstant('{commonappdata}\\DairyOS');" in source
    install_lines = [
        line for line in source.splitlines()
        if line.startswith("Source:") and "recovery" in line.lower()
    ]
    assert install_lines
    for line in install_lines:
        assert 'DestDir: "{commonappdata}\\DairyOS-Recovery\\' in line
        assert 'DestDir: "{commonappdata}\\DairyOS\\' not in line
    install_delete = source[source.index("[InstallDelete]"):source.index("[Code]")]
    assert 'Type: filesandordirs; Name: "{commonappdata}\\DairyOS\\recovery"' in install_delete
    existing_state = source[
        source.index("function CanonicalDairyOSDataRootHasExistingState(): Boolean;"):
        source.index("function ExistingDairyOSInstallationMatches(): Boolean;")
    ]
    assert "CompareText(FindRec.Name, 'recovery') <> 0" in existing_state
