from pathlib import Path

import pytest

from dairyos.admin import auth


def _root(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(auth.time, "sleep", lambda _seconds: None)


def test_first_run_setup_stores_only_verifiers_and_issues_recovery(monkeypatch, tmp_path):
    _root(monkeypatch, tmp_path)
    recovery = auth.setup("Correct-Horse-Battery-1", "Correct-Horse-Battery-1")

    text = auth.auth_state_path().read_text(encoding="utf-8")
    assert "Correct-Horse-Battery-1" not in text
    assert recovery not in text
    assert auth.verify_password("Correct-Horse-Battery-1")
    assert not auth.verify_password("wrong-password")


def test_change_password_rotates_recovery_key(monkeypatch, tmp_path):
    _root(monkeypatch, tmp_path)
    first = auth.setup("Initial-Admin-Password-1", "Initial-Admin-Password-1")
    second = auth.change_password(
        "Initial-Admin-Password-1",
        "Replacement-Password-2",
        "Replacement-Password-2",
    )

    assert first != second
    assert not auth.verify_password("Initial-Admin-Password-1")
    assert auth.verify_password("Replacement-Password-2")
    with pytest.raises(auth.AdminAuthenticationError, match="Recovery key is invalid"):
        auth.recover_password(
            first,
            "Another-Password-3",
            "Another-Password-3",
        )


def test_recovery_resets_password_and_rotates_key(monkeypatch, tmp_path):
    _root(monkeypatch, tmp_path)
    first = auth.setup("Initial-Admin-Password-1", "Initial-Admin-Password-1")
    second = auth.recover_password(
        first,
        "Recovered-Password-2",
        "Recovered-Password-2",
    )

    assert second != first
    assert auth.verify_password("Recovered-Password-2")
    with pytest.raises(auth.AdminAuthenticationError):
        auth.recover_password(
            first,
            "Third-Password-3",
            "Third-Password-3",
        )


def test_password_policy_and_confirmation(monkeypatch, tmp_path):
    _root(monkeypatch, tmp_path)
    with pytest.raises(auth.AdminAuthenticationError, match="at least"):
        auth.setup("short", "short")
    with pytest.raises(auth.AdminAuthenticationError, match="confirmation"):
        auth.setup("Long-Enough-Password", "Different-Password")


def test_audit_records_authentication(monkeypatch, tmp_path):
    _root(monkeypatch, tmp_path)
    auth.setup("Initial-Admin-Password-1", "Initial-Admin-Password-1")
    auth.verify_password("bad")
    auth.verify_password("Initial-Admin-Password-1")

    events = auth.read_audit()
    assert any(row["event"] == "admin-login" and not row["success"] for row in events)
    assert any(row["event"] == "admin-login" and row["success"] for row in events)
