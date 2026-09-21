import inspect
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dairyos.email.digest import DashboardDigestService

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_API = (ROOT / "src/dairyos/api/settings.py").read_text(encoding="utf-8")
SETTINGS_UI = (
    ROOT / "src/DairyOS.Web/src/components/SettingsTab.tsx"
).read_text(encoding="utf-8")


def test_manual_snapshot_uses_canonical_daily_summary_pdf_delivery():
    source = inspect.getsource(DashboardDigestService.send_snapshot)
    assert "_pdf_payload" in source
    assert "_delivery_content" in source
    assert "daily_summary_pdf(summary)" in source
    assert "DairyOS-Daily-Summary-" in source
    assert '"application"' in source
    assert '"pdf"' in source

def test_manual_snapshot_delivery_does_not_consume_nightly_digest_run():
    source = inspect.getsource(DashboardDigestService.send_snapshot)
    assert "EmailDigestRun" not in source
    assert "EmailDigestDelivery" not in source
    assert "send_for_date" not in source
    assert "MANUAL_SNAPSHOT" in source
    assert "recipient_ids" in source


def test_snapshot_endpoint_and_recipient_selection_are_wired_to_existing_email_settings():
    assert '@router.post("/email/snapshot")' in SETTINGS_API
    assert "DashboardDigestService(container=container).send_snapshot" in SETTINGS_API
    assert "recipient_ids=payload.recipient_ids" in SETTINGS_API

    assert "Share Daily Summary" in SETTINGS_UI
    assert "Select All for Daily Summary" in SETTINGS_UI
    assert "/settings/email/snapshot" in SETTINGS_UI
    assert "recipient_ids: selectedRecipientIds" in SETTINGS_UI
    assert "does not replace or suppress the automatic nightly summary" in SETTINGS_UI
    assert "governed Daily Summary PDF" in SETTINGS_UI
    assert "Share DairyOS Snapshot" not in SETTINGS_UI
    assert "Select All for Snapshot" not in SETTINGS_UI
