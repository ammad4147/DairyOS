from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"


def test_installer_provisions_pg_ctl_in_application_owned_recovery_folder():
    source = INSTALLER.read_text(encoding="utf-8")
    recovery_root = "{commonappdata}\\DairyOS\\recovery\\PostgreSQL\\bin"
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
    assert "{commonappdata}\\DairyOS\\recovery\\PostgreSQL\\bin\\pg_ctl.exe" in recovery
