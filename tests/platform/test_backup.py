from pathlib import Path

import pytest

from dairyos.platform import backup


def test_create_backup_writes_checksum_manifest(monkeypatch, tmp_path):
    dump = tmp_path / "dairyos.dump"

    monkeypatch.setattr(backup, "_require_tool", lambda name: "/usr/bin/pg_dump")
    monkeypatch.setattr(
        backup,
        "_database_url",
        lambda: "postgresql+psycopg://postgres:secret@localhost:5432/dairyos",
    )

    def fake_run(command, **kwargs):
        dump.write_bytes(b"verified dump payload")
        return type("Completed", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr(backup.subprocess, "run", fake_run)

    manifest_path = backup.create_backup(tmp_path)
    manifest = manifest_path.read_text(encoding="utf-8")

    assert '"backup_file": "dairyos.dump"' in manifest
    assert '"sha256":' in manifest
    assert '"size_bytes": 21' in manifest


def test_restore_rejects_checksum_mismatch(monkeypatch, tmp_path):
    dump = tmp_path / "dairyos.dump"
    dump.write_bytes(b"not the recorded payload")
    (tmp_path / "manifest.json").write_text(
        '{"backup_file":"dairyos.dump","sha256":"invalid"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(backup, "_require_tool", lambda name: "/usr/bin/pg_restore")

    with pytest.raises(backup.BackupError, match="checksum verification failed"):
        backup.restore_backup(tmp_path)


def test_restore_executes_only_after_checksum_verification(monkeypatch, tmp_path):
    dump = tmp_path / "dairyos.dump"
    dump.write_bytes(b"verified dump payload")
    checksum = backup._checksum(dump)
    (tmp_path / "manifest.json").write_text(
        '{"backup_file":"dairyos.dump","sha256":"%s"}\n' % checksum,
        encoding="utf-8",
    )
    monkeypatch.setattr(backup, "_require_tool", lambda name: "/usr/bin/pg_restore")
    monkeypatch.setattr(
        backup,
        "_database_url",
        lambda: "postgresql+psycopg://postgres:secret@localhost:5432/dairyos",
    )
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return type("Completed", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr(backup.subprocess, "run", fake_run)
    backup.restore_backup(tmp_path)

    assert calls
    assert "--clean" in calls[0]
    assert "--if-exists" in calls[0]
    assert "--no-owner" in calls[0]
