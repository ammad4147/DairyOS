import pytest

from dairyos.api.auth import _decode_token, _hash_password, _issue_token, _verify_password
from dairyos.application.identity.models.authorization_role import AuthorizationRole


def test_password_hash_is_salted_and_verifiable():
    encoded = _hash_password("correct horse battery staple")

    assert encoded != "correct horse battery staple"
    assert _verify_password("correct horse battery staple", encoded)
    assert not _verify_password("wrong password", encoded)


def test_password_hashes_use_distinct_salts():
    first = _hash_password("same password")
    second = _hash_password("same password")

    assert first != second
    assert _verify_password("same password", first)
    assert _verify_password("same password", second)


def test_signed_token_round_trips(monkeypatch):
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")
    context = {
        "sub": "worker-1",
        "farm_id": "farm-1",
        "role": AuthorizationRole.MILKER.value,
    }

    token = _issue_token(context)
    decoded = _decode_token(token)

    assert decoded["sub"] == "worker-1"
    assert decoded["farm_id"] == "farm-1"
    assert decoded["role"] == "milker"
    assert decoded["exp"] > 0


def test_tampered_token_is_rejected(monkeypatch):
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")
    token = _issue_token({"sub": "worker-1", "farm_id": "farm-1", "role": "milker"})
    encoded, signature = token.split(".", 1)
    tampered = encoded + "x" + "." + signature

    with pytest.raises(Exception):
        _decode_token(tampered)
