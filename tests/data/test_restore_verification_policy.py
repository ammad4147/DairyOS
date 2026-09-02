from datetime import datetime, timedelta, timezone
import json

from dairyos.data.database import restore_verification


def _write_health(tmp_path, payload):
    path = tmp_path / "backups" / "backup-health.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_restore_verification_is_due_when_never_recorded(tmp_path):
    assert restore_verification.restore_verification_due(
        tmp_path,
        now=datetime(2026, 9, 2, tzinfo=timezone.utc),
    ) is True


def test_restore_verification_is_not_due_inside_seven_days(tmp_path):
    now = datetime(2026, 9, 9, 12, tzinfo=timezone.utc)
    _write_health(
        tmp_path,
        {"last_restore_verification": (now - timedelta(days=6)).isoformat()},
    )

    assert restore_verification.restore_verification_due(tmp_path, now=now) is False


def test_restore_verification_is_due_after_seven_days(tmp_path):
    now = datetime(2026, 9, 9, 12, tzinfo=timezone.utc)
    _write_health(
        tmp_path,
        {"last_restore_verification": (now - timedelta(days=7)).isoformat()},
    )

    assert restore_verification.restore_verification_due(tmp_path, now=now) is True
