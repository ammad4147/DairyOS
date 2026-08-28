from __future__ import annotations

import os

from dairyos.farm.settings.services.deployment_control_service import (
    DEPLOYMENT_ACTIVE_KEY,
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
    def __init__(self, repository):
        self.repository = repository


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


def test_deploy_requires_literal_confirmation_at_api_boundary_only(monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    repository = FakeRepository()
    settings = FakeSettings(repository)
    service = DeploymentControlService(settings)

    status = service.activate(updated_by="TEST")
    assert status["deployed"] is True
    assert repository.get(DEPLOYMENT_ACTIVE_KEY) == "true"


def test_reset_deactivates_without_password(monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    repository = FakeRepository()
    repository.set(DEPLOYMENT_ACTIVE_KEY, "true")
    settings = FakeSettings(repository)
    service = DeploymentControlService(settings)

    status = service.deactivate(updated_by="TEST")
    assert status["deployed"] is False
    assert repository.get(DEPLOYMENT_ACTIVE_KEY) == "false"
