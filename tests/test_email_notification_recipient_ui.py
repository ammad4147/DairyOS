from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "src/DairyOS.Web/src/components/SettingsTab.tsx").read_text(encoding="utf-8")


def test_notification_recipients_use_backend_authority_not_localstorage():
    assert "/settings/email/recipients" in SETTINGS
    assert "dairyos_notification_recipients" not in SETTINGS
    assert "localStorage.setItem(RECIPIENT_KEY" not in SETTINGS
