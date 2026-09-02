from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from dairyos.data.database import automatic_backups as backups


def _fake_backup_tooling(monkeypatch):
    def create_backup(database_url: str, destination: Path):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"DairyOS verified PostgreSQL backup payload")
        return destination

    def verify_archive(path: Path):
        return {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": "abc123",
            "archive_verified": "true",
        }

    def verify_checksum(path: Path, expected: str):
        assert path.is_file()
        assert expected == "abc123"
        return {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": expected,
        }

    monkeypatch.setattr(backups, "create_backup", create_backup)
    monkeypatch.setattr(backups, "verify_backup_archive", verify_archive)
    monkeypatch.setattr(backups, "verify_backup_checksum", verify_checksum)


def test_automatic_backup_creates_primary_mirror_and_monthly_archive(monkeypatch, tmp_path):
    _fake_backup_tooling(monkeypatch)
    data_root = tmp_path / "data"
    mirror_root = tmp_path / "second-drive" / "DairyOS-Backups"
    destination = backups.BackupDestination(
        root=mirror_root,
        physically_redundant=True,
    )

    result = backups.run_automatic_backup(
        "postgresql+psycopg://backup-role@localhost/dairyos",
        data_root=data_root,
        mirror_destination=destination,
        now=datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc),
    )

    assert result.primary.name == "DairyOS-Auto-20260902T120000Z.dump"
    assert result.primary.is_file()
    assert result.mirror.is_file()
    assert result.monthly_primary is not None
    assert result.monthly_primary.name == "DairyOS-Monthly-2026-09-20260902T120000Z.dump"
    assert result.monthly_primary.is_file()
    assert result.monthly_mirror is not None and result.monthly_mirror.is_file()
    assert result.physically_redundant is True

    health = json.loads(result.health_path.read_text(encoding="utf-8"))
    assert health["status"] == "HEALTHY"
    assert health["archive_verified"] is True
    assert health["physically_redundant"] is True
    assert health["rolling_retention"] == 120
    assert health["monthly_retention"] == 60


def test_only_one_monthly_archive_is_created_per_calendar_month(monkeypatch, tmp_path):
    _fake_backup_tooling(monkeypatch)
    data_root = tmp_path / "data"
    destination = backups.BackupDestination(
        root=tmp_path / "mirror",
        physically_redundant=False,
        degraded_reason="same disk",
    )

    first = backups.run_automatic_backup(
        "postgresql+psycopg://backup-role@localhost/dairyos",
        data_root=data_root,
        mirror_destination=destination,
        now=datetime(2026, 9, 1, 1, 0, tzinfo=timezone.utc),
    )
    second = backups.run_automatic_backup(
        "postgresql+psycopg://backup-role@localhost/dairyos",
        data_root=data_root,
        mirror_destination=destination,
        now=datetime(2026, 9, 15, 1, 0, tzinfo=timezone.utc),
    )

    assert first.monthly_primary is not None
    assert second.monthly_primary is None
    assert len(list((data_root / "backups" / "monthly").glob("DairyOS-Monthly-2026-09-*.dump"))) == 1

    health = json.loads(second.health_path.read_text(encoding="utf-8"))
    assert health["status"] == "DEGRADED"
    assert health["degraded_reason"] == "same disk"


def test_failed_backup_records_failure_without_erasing_last_success(monkeypatch, tmp_path):
    data_root = tmp_path / "data"
    health_path = backups.backup_health_path(data_root)
    health_path.parent.mkdir(parents=True, exist_ok=True)
    health_path.write_text(
        json.dumps(
            {
                "status": "HEALTHY",
                "last_successful_backup": "2026-09-01T00:00:00Z",
                "physically_redundant": True,
            }
        ),
        encoding="utf-8",
    )

    def fail(*args, **kwargs):
        raise RuntimeError("simulated pg_dump failure")

    monkeypatch.setattr(backups, "create_backup", fail)

    with pytest.raises(Exception, match="simulated pg_dump failure"):
        backups.run_automatic_backup(
            "postgresql+psycopg://backup-role@localhost/dairyos",
            data_root=data_root,
            mirror_destination=backups.BackupDestination(tmp_path / "mirror", True),
            now=datetime(2026, 9, 2, 0, 0, tzinfo=timezone.utc),
        )

    health = json.loads(health_path.read_text(encoding="utf-8"))
    assert health["status"] == "FAILED"
    assert health["last_successful_backup"] == "2026-09-01T00:00:00Z"
