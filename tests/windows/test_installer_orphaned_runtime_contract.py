from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"


def test_installer_extracts_pg_ctl_before_retained_data_recovery():
    source = INSTALLER.read_text(encoding="utf-8")
    assert 'Source: "{#BundlePath}\\runtime\\PostgreSQL\\bin\\pg_ctl.exe"; Flags: dontcopy' in source
    build = (ROOT / "scripts" / "Build-DairyOS-Installer.ps1").read_text(encoding="utf-8-sig")
    assert '"/DBundlePath=" + $bundlePath' in build
    recovery = source[source.index("function StopInstalledDairyOSForUninstall(): Boolean;"):]
    assert "ExtractTemporaryFile('pg_ctl.exe')" in recovery
    assert "{tmp}\\pg_ctl.exe" in recovery
