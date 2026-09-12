from __future__ import annotations

from pathlib import Path

import pytest

from dairyos.windows import supervisor
from dairyos.windows.installation_choice import (
    InstallationChoiceError,
    read_pending_installation_choice,
    write_pending_installation_choice,
)


def test_installation_choice_round_trips_atomically(tmp_path):
    root = tmp_path / "DairyOS"

    target = write_pending_installation_choice(root, mode="clean")

    assert target == root / "pending-installation-choice.json"
    choice = read_pending_installation_choice(root)
    assert choice is not None
    assert choice.mode == "clean"
    assert choice.backup_path is None
    assert choice.requested_at.endswith("Z")


def test_restore_choice_requires_an_explicit_path(tmp_path):
    with pytest.raises(InstallationChoiceError, match="explicit backup path"):
        write_pending_installation_choice(tmp_path, mode="restore")


def test_clean_choice_cannot_carry_a_backup(tmp_path):
    with pytest.raises(InstallationChoiceError, match="cannot include"):
        write_pending_installation_choice(
            tmp_path,
            mode="clean",
            backup_path=tmp_path / "backup",
        )


def test_keep_choice_round_trips_without_a_backup(tmp_path):
    write_pending_installation_choice(tmp_path, mode="keep")

    choice = read_pending_installation_choice(tmp_path)

    assert choice is not None
    assert choice.mode == "keep"
    assert choice.backup_path is None


def test_new_choice_round_trips_without_a_backup(tmp_path):
    write_pending_installation_choice(tmp_path, mode="new")

    choice = read_pending_installation_choice(tmp_path)

    assert choice is not None
    assert choice.mode == "new"
    assert choice.backup_path is None


def test_new_choice_is_non_destructive_when_applied(monkeypatch, tmp_path):
    root = tmp_path / "DairyOS"
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(root))
    (root / "logs").mkdir(parents=True)
    (root / "logs" / "historical.log").write_text("keep", encoding="utf-8")
    (root / "storage").mkdir()
    (root / "storage" / "history.json").write_text("{}", encoding="utf-8")
    (root / "backups").mkdir()
    (root / "backups" / "retained-backup").mkdir()
    write_pending_installation_choice(root, mode="new")

    supervisor.process_pending_installation_choice()

    assert read_pending_installation_choice(root) is None
    assert (root / "logs" / "historical.log").read_text(encoding="utf-8") == "keep"
    assert (root / "storage" / "history.json").read_text(encoding="utf-8") == "{}"
    assert (root / "backups" / "retained-backup").is_dir()


def test_supervisor_stages_explicit_clean_choice(monkeypatch, tmp_path):
    root = tmp_path / "DairyOS"
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(root))

    assert supervisor.main(
        [
            "--lifecycle-choice",
            "--choice-mode",
            "clean",
            "--data-root",
            str(root),
        ]
    ) == 0

    choice = read_pending_installation_choice(root)
    assert choice is not None
    assert choice.mode == "clean"


def test_supervisor_keep_choice_clears_an_abandoned_request(monkeypatch, tmp_path):
    root = tmp_path / "DairyOS"
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(root))
    write_pending_installation_choice(root, mode="keep")

    supervisor.process_pending_installation_choice(restore_only=True)

    assert read_pending_installation_choice(root) is None


def test_failed_restore_retains_the_one_shot_request(monkeypatch, tmp_path):
    root = tmp_path / "DairyOS"
    selected = tmp_path / "recovery" / "selected.dump"
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(root))
    write_pending_installation_choice(root, mode="restore", backup_path=selected)

    class Candidate:
        path = selected.resolve()

    class Lease:
        manager = object()

        def close(self):
            pass

    class FailingAdminService:
        def __init__(self, _manager):
            pass

        def restore(self, _path):
            raise RuntimeError("restore failed")

    monkeypatch.setattr(
        "dairyos.admin.backup_catalog.verify_restore_candidate",
        lambda _path: Candidate(),
    )
    monkeypatch.setattr(
        "dairyos.admin.database.acquire_admin_database",
        lambda *_args, **_kwargs: Lease(),
    )
    monkeypatch.setattr("dairyos.admin.service.AdminService", FailingAdminService)

    with pytest.raises(RuntimeError, match="restore failed"):
        supervisor.process_pending_installation_choice(restore_only=True)

    retained = read_pending_installation_choice(root)
    assert retained is not None
    assert retained.mode == "restore"
    assert retained.backup_path == selected.resolve()


def test_supervisor_stages_only_the_reverified_restore_path(monkeypatch, tmp_path):
    root = tmp_path / "DairyOS"
    selected = tmp_path / "recovery" / "selected.dump"
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(root))

    class Candidate:
        path = selected.resolve()

    calls = []
    monkeypatch.setattr(
        "dairyos.admin.backup_catalog.verify_restore_candidate",
        lambda path: calls.append(Path(path)) or Candidate(),
    )

    assert supervisor.main(
        [
            "--lifecycle-choice",
            "--choice-mode",
            "restore",
            "--backup-path",
            str(selected),
            "--data-root",
            str(root),
        ]
    ) == 0

    choice = read_pending_installation_choice(root)
    assert choice is not None
    assert choice.mode == "restore"
    assert choice.backup_path == selected.resolve()
    assert calls == [selected.resolve()]
