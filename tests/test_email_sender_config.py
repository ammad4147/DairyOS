import os

import pytest

from dairyos.email.crypto import encrypt_secret, decrypt_secret


def test_email_secret_round_trip(monkeypatch):
    monkeypatch.setenv("DAIRYOS_EMAIL_SECRET", "test-email-secret")
    ciphertext = encrypt_secret("smtp-password")
    assert ciphertext
    assert ciphertext != "smtp-password"
    assert decrypt_secret(ciphertext) == "smtp-password"


def test_email_secret_requires_deployment_secret(monkeypatch):
    monkeypatch.delenv("DAIRYOS_EMAIL_SECRET", raising=False)
    monkeypatch.delenv("DAIRYOS_AUTH_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        encrypt_secret("smtp-password")
