from pathlib import Path
import json
import pytest
from dairyos.admin.service import AdminService, RESET_CONFIRMATION
from dairyos.lifecycle.manager import LifecycleError


class FakeManager:
    database_url = None

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.calls = []

    def validate(self, require_database=True):
        self.calls.append(("validate", require_database))
        return {"valid": True}

    def backup(self, label="pre-change"):
        self.calls.append(("backup", label))
        path = self.tmp_path / label
        path.mkdir(parents=True, exist_ok=True)
        (path / "backup.json").write_text(json.dumps({"files": []}), encoding="utf-8")
        return path

    def rollback(self, backup):
        self.calls.append(("rollback", backup))
        return {"valid": True}

    def uninstall(self, mode, confirmation=None):
        self.calls.append(("uninstall", mode, confirmation))


def test_backup_delegates_to_canonical_lifecycle_manager(tmp_path):
    manager = FakeManager(tmp_path)
    result = AdminService(manager).backup("operator")
    assert result.success is True
    assert manager.calls == [("backup", "operator")]


def test_reset_requires_exact_confirmation(tmp_path):
    manager = FakeManager(tmp_path)
    with pytest.raises(LifecycleError):
        AdminService(manager).reset("wrong")
    assert manager.calls == []


def test_reset_requires_database_before_backup_or_mutation(tmp_path):
    manager = FakeManager(tmp_path)
    with pytest.raises(LifecycleError, match="DAIRYOS_DATABASE_URL"):
        AdminService(manager).reset(RESET_CONFIRMATION)
    assert manager.calls == []


def test_reset_requires_a_verified_backup(tmp_path, monkeypatch):
    manager = FakeManager(tmp_path)
    manager.database_url = "postgresql+psycopg://example"
    monkeypatch.setattr(manager, "validate", lambda require_database=True: {"valid": True})
    monkeypatch.setattr("dairyos.admin.service._assert_runtime_stopped", lambda: None)
    monkeypatch.setattr(
        "dairyos.admin.service._record_database_checksum",
        lambda path: (_ for _ in ()).throw(LifecycleError("PostgreSQL backup verification failed.")),
    )
    with pytest.raises(LifecycleError, match="PostgreSQL backup"):
        AdminService(manager).reset(RESET_CONFIRMATION)
    assert manager.calls == [("backup", "pre-reset")]


def test_reset_delegates_mutation_to_lifecycle_coordinator(tmp_path, monkeypatch):
    manager = FakeManager(tmp_path)
    manager.database_url = "postgresql+psycopg://example"
    monkeypatch.setattr("dairyos.admin.service._assert_runtime_stopped", lambda: None)
    monkeypatch.setattr("dairyos.admin.service._record_database_checksum", lambda path: None)
    monkeypatch.setattr("dairyos.admin.service._verify_backup_directory", lambda path: None)
    monkeypatch.setattr("dairyos.admin.service._copy_external_recovery_artifact", lambda path: path)
    monkeypatch.setattr("dairyos.admin.service._write_audit_event", lambda *args, **kwargs: None)

    class Execution:
        tables_cleared = ("animals", "milk_production")

    called = []
    monkeypatch.setattr(
        "dairyos.admin.service.reset_operational_data",
        lambda url, updated_by: (called.append((url, updated_by)) or Execution()),
    )
    monkeypatch.setattr("dairyos.admin.service.verify_zero_state", lambda url: {})
    result = AdminService(manager).reset(RESET_CONFIRMATION)
    assert result.success is True
    assert called == [("postgresql+psycopg://example", "DairyOS Admin Tool")]
    assert manager.calls == [("validate", True), ("backup", "pre-reset")]