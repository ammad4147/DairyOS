from __future__ import annotations

import pytest

from dairyos.windows.components import (
    ComponentAction,
    ComponentSpec,
    ComponentError,
    apply_component,
    compare_versions,
    inspect_component,
    normalize_version,
)


def _spec(
    installed: str | None,
    bundled: str = "18.6",
    update=None,
):
    calls = {"install": 0, "update": 0}

    def detect():
        return installed

    def install():
        calls["install"] += 1

    def perform_update():
        calls["update"] += 1

    spec = ComponentSpec(
        key="postgresql",
        display_name="PostgreSQL",
        bundled_version=bundled,
        detect_version=detect,
        install=install,
        update=update or perform_update,
    )
    return spec, calls


def test_normalize_version():
    assert normalize_version("18.6") == (18, 6)
    assert normalize_version("v18.6.1") == (18, 6, 1)


def test_compare_versions():
    assert compare_versions("18.5", "18.6") < 0
    assert compare_versions("18.6", "18.6") == 0
    assert compare_versions("18.7", "18.6") > 0


def test_missing_component_is_fresh_install():
    spec, calls = _spec(None)

    inspection = inspect_component(spec)

    assert inspection.action is ComponentAction.FRESH_INSTALL
    assert "not installed" in inspection.notification.lower()

    result = apply_component(spec)

    assert result.action is ComponentAction.FRESH_INSTALL
    assert calls["install"] == 1


def test_same_version_is_retained():
    spec, calls = _spec("18.6")

    inspection = inspect_component(spec)

    assert inspection.action is ComponentAction.RETAIN_EXISTING
    assert calls["install"] == 0
    assert calls["update"] == 0
    assert "retained" in inspection.notification.lower()


def test_newer_installed_version_is_retained():
    spec, calls = _spec("18.7")

    inspection = inspect_component(spec)

    assert inspection.action is ComponentAction.RETAIN_NEWER
    assert calls["install"] == 0
    assert calls["update"] == 0
    assert "18.7" in inspection.notification
    assert "18.6" in inspection.notification


def test_older_installed_version_is_updated():
    spec, calls = _spec("18.5")

    inspection = inspect_component(spec)

    assert inspection.action is ComponentAction.UPDATE
    assert "18.5" in inspection.notification
    assert "18.6" in inspection.notification

    result = apply_component(spec)

    assert result.action is ComponentAction.UPDATE
    assert calls["update"] == 1


def test_old_version_without_update_path_is_blocked():
    spec, calls = _spec("18.5", update=lambda: None)
    spec = ComponentSpec(
        key=spec.key,
        display_name=spec.display_name,
        bundled_version=spec.bundled_version,
        detect_version=spec.detect_version,
        install=spec.install,
        update=None,
    )

    inspection = inspect_component(spec)

    assert inspection.action is ComponentAction.BLOCKED

    with pytest.raises(ComponentError):
        apply_component(spec)

    assert calls["install"] == 0


def test_incompatible_existing_version_is_blocked():
    spec, calls = _spec("17.9")
    spec = ComponentSpec(
        key=spec.key,
        display_name=spec.display_name,
        bundled_version=spec.bundled_version,
        detect_version=spec.detect_version,
        install=spec.install,
        update=spec.update,
        is_compatible=lambda version: version.startswith("18."),
    )

    inspection = inspect_component(spec)

    assert inspection.action is ComponentAction.BLOCKED
    assert "not compatible" in inspection.notification.lower()

    with pytest.raises(ComponentError):
        apply_component(spec)

    assert calls["install"] == 0
    assert calls["update"] == 0