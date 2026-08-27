from __future__ import annotations

import os

import pytest

from dairyos.farm.settings.services.deployment_control_service import (
    DEPLOYMENT_ACTIVE_KEY,
    DeploymentControlError,
    DeploymentControlService,
)


class FakeRepository:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, updated_by=None):
        self.values[key] = value


class FakeSettings:
    def __init__(self, repository, password_ok=False):
        self.repository = repository
        self.password_ok = password_ok

    def is_reset_protected(self):
        return self.password_ok

    def verify_reset_password(self, password):
        return self.password_ok and password == "correct-password"


def test_production_defaults_to_not_deployed(monkeypatch):
    repository = FakeRepository()
    settings = FakeSettings(repository)
    monkeypatch.setenv("DAIRYOS_ENV", "production")

    assert DeploymentControlService(settings).is_deployed() is False
    assert repository.get(DEPLOYMENT_ACTIVE_KEY) is None


def test_development_defaults_to_deployed(monkeypatch):
    repository = FakeRepository()
    settings = FakeSettings(repository)
    monkeypatch.setenv("DAIRYOS_ENV", "development")

    assert DeploymentControlService(settings).is_deployed() is True


def test_deploy_requires_password(monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    repository = FakeRepository()
    settings = FakeSettings(repository, password_ok=True)
    service = DeploymentControlService(settings)

    with pytest.raises(DeploymentControlError):
        service.activate(password="wrong", updated_by="TEST")

    status = service.activate(password="correct-password", updated_by="TEST")
    assert status["deployed"] is True
    assert repository.get(DEPLOYMENT_ACTIVE_KEY) == "true"


def test_reset_requires_password_and_deactivates(monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    repository = FakeRepository()
    repository.set(DEPLOYMENT_ACTIVE_KEY, "true")
    settings = FakeSettings(repository, password_ok=True)
    service = DeploymentControlService(settings)

    with pytest.raises(DeploymentControlError):
        service.deactivate(password="wrong", updated_by="TEST")

    status = service.deactivate(password="correct-password", updated_by="TEST")
    assert status["deployed"] is False
    assert repository.get(DEPLOYMENT_ACTIVE_KEY) == "false"
