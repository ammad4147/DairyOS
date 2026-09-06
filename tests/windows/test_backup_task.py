from __future__ import annotations

from types import SimpleNamespace

import pytest

from dairyos.windows import backup_task


def test_existing_scheduled_task_is_verified_without_create(monkeypatch):
    monkeypatch.setattr(backup_task.os, "name", "nt", raising=False)
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[:3] == ["schtasks.exe", "/Query", "/TN"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(f"Unexpected privileged task command: {command}")

    monkeypatch.setattr(backup_task.subprocess, "run", fake_run)
    backup_task.ensure_scheduled_backup_task(run_immediately=True)
    assert calls == [["schtasks.exe", "/Query", "/TN", backup_task.TASK_NAME]]


def test_missing_installer_task_blocks_with_repair_instruction(monkeypatch):
    monkeypatch.setattr(backup_task.os, "name", "nt", raising=False)
    monkeypatch.setattr(
        backup_task.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="ERROR: not found"),
    )
    with pytest.raises(backup_task.BackupTaskError, match="Repair or reinstall"):
        backup_task.ensure_scheduled_backup_task()


def test_runtime_never_uses_schtasks_create_or_run(monkeypatch):
    monkeypatch.setattr(backup_task.os, "name", "nt", raising=False)
    seen = []

    def fake_run(command, **kwargs):
        seen.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(backup_task.subprocess, "run", fake_run)
    backup_task.ensure_scheduled_backup_task(run_immediately=True)
    flattened = " ".join(" ".join(cmd) for cmd in seen)
    assert "/Create" not in flattened
    assert "/Run" not in flattened
