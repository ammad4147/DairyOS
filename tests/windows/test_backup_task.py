from __future__ import annotations

from types import SimpleNamespace

import pytest

from dairyos.windows import backup_task


TASK_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<Task xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Actions Context="Author">
    <Exec>
      <Command>{command}</Command>
      {arguments}
    </Exec>
  </Actions>
</Task>
"""


def _task_xml(command: str, arguments: str | None = None) -> str:
    argument_xml = (
        f"<Arguments>{arguments}</Arguments>"
        if arguments is not None
        else ""
    )
    return TASK_XML_TEMPLATE.format(command=command, arguments=argument_xml)


def test_existing_scheduled_task_requires_exact_structured_action(monkeypatch, tmp_path):
    monkeypatch.setattr(backup_task.os, "name", "nt", raising=False)
    executable = tmp_path / "DairyOSBackup.exe"
    executable.write_bytes(b"backup")
    monkeypatch.setattr(backup_task, "packaged_backup_executable", lambda: executable.resolve())
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout=_task_xml(str(executable)), stderr="")

    monkeypatch.setattr(backup_task.subprocess, "run", fake_run)
    backup_task.ensure_scheduled_backup_task(run_immediately=True)
    assert calls == [["schtasks.exe", "/Query", "/TN", backup_task.TASK_NAME, "/XML"]]
    assert backup_task.scheduled_backup_task_exists() is True


def test_missing_installer_task_blocks_with_repair_instruction(monkeypatch):
    monkeypatch.setattr(backup_task.os, "name", "nt", raising=False)
    monkeypatch.setattr(
        backup_task.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="ERROR: not found"),
    )
    with pytest.raises(backup_task.BackupTaskError, match="Repair or reinstall"):
        backup_task.ensure_scheduled_backup_task()


@pytest.mark.parametrize(
    ("command", "arguments"),
    [
        (r"C:\Program", r"Files\DairyOS\DairyOSBackup.exe"),
        (r"C:\Program Files\DairyOS\DairyOSBackup.exe", "--unexpected"),
    ],
)
def test_malformed_scheduled_task_action_fails_closed(monkeypatch, tmp_path, command, arguments):
    monkeypatch.setattr(backup_task.os, "name", "nt", raising=False)
    executable = tmp_path / "DairyOSBackup.exe"
    executable.write_bytes(b"backup")
    monkeypatch.setattr(backup_task, "packaged_backup_executable", lambda: executable.resolve())
    monkeypatch.setattr(
        backup_task.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=_task_xml(command, arguments), stderr=""),
    )
    assert backup_task.scheduled_backup_task_exists() is False
    with pytest.raises(backup_task.BackupTaskError, match="misconfigured"):
        backup_task.ensure_scheduled_backup_task()


def test_runtime_never_uses_schtasks_create_or_run(monkeypatch, tmp_path):
    monkeypatch.setattr(backup_task.os, "name", "nt", raising=False)
    executable = tmp_path / "DairyOSBackup.exe"
    executable.write_bytes(b"backup")
    monkeypatch.setattr(backup_task, "packaged_backup_executable", lambda: executable.resolve())
    seen = []

    def fake_run(command, **kwargs):
        seen.append(command)
        return SimpleNamespace(returncode=0, stdout=_task_xml(str(executable)), stderr="")

    monkeypatch.setattr(backup_task.subprocess, "run", fake_run)
    backup_task.ensure_scheduled_backup_task(run_immediately=True)
    flattened = " ".join(" ".join(cmd) for cmd in seen)
    assert "/Create" not in flattened
    assert "/Run" not in flattened
