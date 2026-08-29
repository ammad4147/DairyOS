from pathlib import Path

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
        return self.tmp_path / label

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
    with pytest.raises(LifecycleError, match="Backup manifest is missing"):
        AdminService(manager).reset(RESET_CONFIRMATION)
    assert manager.calls == [("backup", "pre-reset")]
