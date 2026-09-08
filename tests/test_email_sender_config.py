import os

import pytest

from dairyos.email.crypto import decrypt_secret, encrypt_secret


def test_email_secret_round_trip(monkeypatch):
    monkeypatch.setenv("DAIRYOS_EMAIL_SECRET", "test-email-secret")
    ciphertext = encrypt_secret("smtp-password")
    assert ciphertext
    assert ciphertext != "smtp-password"
    assert decrypt_secret(ciphertext) == "smtp-password"


def test_email_secret_requires_deployment_secret(monkeypatch):
    from types import SimpleNamespace

    from dairyos.email import crypto

    monkeypatch.setattr(crypto, "os", SimpleNamespace(name="posix", getenv=os.getenv))
    monkeypatch.delenv("DAIRYOS_EMAIL_SECRET", raising=False)
    monkeypatch.delenv("DAIRYOS_AUTH_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        encrypt_secret("smtp-password")


@pytest.mark.skipif(os.name != "nt", reason="Requires actual Windows DPAPI")
def test_windows_email_secret_needs_no_deployment_secret(monkeypatch):
    import json

    monkeypatch.delenv("DAIRYOS_EMAIL_SECRET", raising=False)
    monkeypatch.delenv("DAIRYOS_AUTH_SECRET", raising=False)
    ciphertext = encrypt_secret("smtp-dpapi-test-password")
    assert "smtp-dpapi-test-password" not in ciphertext
    assert json.loads(ciphertext)["scheme"] == "windows-dpapi-user"
    assert decrypt_secret(ciphertext) == "smtp-dpapi-test-password"


def test_legacy_email_ciphertext_remains_readable(monkeypatch):
    from dairyos.email.crypto import _fernet

    monkeypatch.setenv("DAIRYOS_EMAIL_SECRET", "legacy-test-secret")
    ciphertext = _fernet().encrypt(b"legacy-password").decode("ascii")
    assert decrypt_secret(ciphertext) == "legacy-password"


@pytest.mark.parametrize(
    "ciphertext",
    [
        '{"version":1,"scheme":"windows-dpapi-user","value":"broken"}',
        '{"version":2,"scheme":"windows-dpapi-user","value":""}',
        '{"version":1,"scheme":"plaintext","value":"password"}',
        "{broken",
    ],
)
def test_corrupt_email_envelopes_fail_safely(ciphertext):
    with pytest.raises(RuntimeError, match="SMTP credential cannot be unlocked"):
        decrypt_secret(ciphertext)


def test_smtp_persistence_preserves_replaces_and_sends_without_public_secret(
    monkeypatch,
):
    import json

    from dairyos.data.database.session import SessionLocal
    from dairyos.data.models.email_sender_setting import EmailSenderSetting
    from dairyos.email.service import EmailService

    monkeypatch.setenv("DAIRYOS_EMAIL_SECRET", "portable-test-secret")
    service = EmailService()
    payload = {
        "sender_email": "farm@example.invalid",
        "smtp_host": "smtp.example.invalid",
        "smtp_username": "farm",
        "smtp_password": "first-test-password",
    }
    calls = []

    class SMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def starttls(self):
            calls.append("tls")

        def login(self, username, password):
            calls.append((username, password))

        def send_message(self, message):
            calls.append(message["To"])

    monkeypatch.setattr("dairyos.email.service.smtplib.SMTP", SMTP)
    try:
        public = service.save_config(payload, "test")
        assert "first-test-password" not in json.dumps(public)
        with SessionLocal() as session:
            ciphertext = session.get(EmailSenderSetting, 1).smtp_password_ciphertext
        assert "first-test-password" not in ciphertext
        payload.pop("smtp_password")
        payload["sender_display_name"] = "Updated name"
        service.save_config(payload, "test")
        assert service.get_config().smtp_password == "first-test-password"
        payload["smtp_password"] = "replacement-test-password"
        service.save_config(payload, "test")
        assert service.get_config().smtp_password == "replacement-test-password"
        service.send(recipient="recipient@example.invalid", subject="test", body="test")
        assert calls == [
            "tls",
            ("farm", "replacement-test-password"),
            "recipient@example.invalid",
        ]
        assert "replacement-test-password" not in json.dumps(service.public_config())
    finally:
        with SessionLocal() as session:
            row = session.get(EmailSenderSetting, 1)
            if row is not None:
                session.delete(row)
                session.commit()
