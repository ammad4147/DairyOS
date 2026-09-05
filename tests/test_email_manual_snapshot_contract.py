from datetime import date, datetime
import inspect
from pathlib import Path
from zoneinfo import ZoneInfo

from dairyos.email.digest import DashboardDigestService


ROOT = Path(__file__).resolve().parents[1]
SETTINGS_API = (ROOT / "src/dairyos/api/settings.py").read_text(encoding="utf-8")
SETTINGS_UI = (
    ROOT / "src/DairyOS.Web/src/components/SettingsTab.tsx"
).read_text(encoding="utf-8")


def test_manual_snapshot_renderer_has_live_identity_and_generation_timestamp(monkeypatch):
    service = DashboardDigestService(container=object())

    def fake_render(*, digest_date, user_permissions):
        assert digest_date == date(2026, 9, 6)
        assert "dashboard.view_finance" in user_permissions
        return (
            "DairyOS Daily Summary — 2026-09-06",
            "DairyOS Daily Summary — 2026-09-06\n"
            "Operational Date: 2026-09-06\n"
            "\n"
            "MILK PRODUCTION\n"
            "Total yield today: 10.0 litres\n"
            "\n"
            "This digest reflects governed DairyOS records for the operational date shown.",
        )

    monkeypatch.setattr(service, "render", fake_render)
    generated_at = datetime(
        2026, 9, 6, 14, 35, 7, tzinfo=ZoneInfo("Asia/Karachi")
    )

    subject, body = service.render_snapshot(
        snapshot_date=date(2026, 9, 6),
        generated_at=generated_at,
        user_permissions={"dashboard.view", "dashboard.view_finance"},
    )

    assert subject == "DairyOS Snapshot — 2026-09-06 14:35 PKT"
    assert body.startswith(
        "DairyOS Snapshot\n"
        "Operational Date: 2026-09-06\n"
        "Snapshot Generated: 2026-09-06 14:35:07 PKT"
    )
    assert "This snapshot reflects governed DairyOS records available at the generation time shown." in body


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

    assert "Share DairyOS Snapshot" in SETTINGS_UI
    assert "Select All for Snapshot" in SETTINGS_UI
    assert "/settings/email/snapshot" in SETTINGS_UI
    assert "recipient_ids: selectedRecipientIds" in SETTINGS_UI
    assert "does not replace or suppress the automatic nightly summary" in SETTINGS_UI
