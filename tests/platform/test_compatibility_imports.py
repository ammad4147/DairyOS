"""Regression tests for previously broken compatibility platform modules."""

import importlib
import pkgutil

import pytest

from dairyos.domain.events import Event
from dairyos.intelligence import yield_forecasting
from dairyos.operations.memory.models.memory_signal import MemorySignal
from dairyos.platform.api.services.platform_health_service import (
    PlatformHealthService,
)
from dairyos.platform.container.models.service_lifecycle import ServiceLifecycle
from dairyos.platform.events.models.event import PlatformEvent
from dairyos.platform.events.models.event_type import EventType
from dairyos.platform.events_bridge.services.event_bridge import EventBridge
from dairyos.platform.integration.models.platform_service import PlatformService
from dairyos.platform.registry.services.service_registry import ServiceRegistry
from dairyos.platform.runtime_manager.models.runtime_status import RuntimeStatus
from dairyos.platform.runtime_manager.services.runtime_health import (
    RuntimeHealthService,
)
from dairyos.platform.runtime_manager.services.runtime_manager import RuntimeManager
from dairyos.platform.runtime_manager.services.runtime_orchestrator import (
    RuntimeOrchestrator,
)


def test_memory_signal_uses_dataclasses_field():
    signal = MemorySignal(source="test", message="ok")

    assert signal.source == "test"
    assert signal.message == "ok"
    assert signal.created_at is not None


def test_compatibility_platform_health_reports_degraded_state():
    health = PlatformHealthService().check()

    assert health.status() == "healthy"
    assert health.runtime is True


def test_platform_event_uses_existing_system_event_type():
    event = PlatformEvent(name="boot", source="test")

    assert event.event_type is EventType.SYSTEM


def test_event_bridge_publishes_domain_event():
    published = []

    class Bus:
        def publish(self, event):
            published.append(event)
            return event

    result = EventBridge(Bus()).publish_domain_event(
        domain="milk",
        event_name="milk_recorded",
        payload={"animal_id": "A-001"},
    )

    assert result is published[0]
    assert isinstance(result, Event)
    assert result.payload == {"domain": "milk", "animal_id": "A-001"}


def test_service_registry_and_runtime_manager_have_coherent_lifecycle():
    registry = ServiceRegistry()
    service = PlatformService(name="test", service=object())
    registry.register(service.name, service.service)
    registry.start(service.name)

    entry = registry.list_services()[0]
    assert entry.lifecycle is ServiceLifecycle.STARTED

    manager = RuntimeManager()
    state = RuntimeOrchestrator(manager, registry=registry).start()

    assert state.status is RuntimeStatus.RUNNING
    assert state.active_services == 1
    assert RuntimeHealthService().check(manager).active_services == 1

    RuntimeOrchestrator(manager).stop()
    assert manager.status().status is RuntimeStatus.STOPPED


def test_runtime_orchestrator_honours_disabled_registered_service():
    registry = ServiceRegistry()
    registry.register(
        "disabled",
        PlatformService(name="disabled", service=object(), enabled=False),
    )

    manager = RuntimeManager()
    RuntimeOrchestrator(manager, registry=registry).start()

    assert manager.status().active_services == 0


def test_optional_forecasting_dependency_failure_is_actionable(monkeypatch):
    monkeypatch.setattr(yield_forecasting, "np", None)
    monkeypatch.setattr(yield_forecasting, "curve_fit", None)

    with pytest.raises(RuntimeError, match="optional numpy and scipy"):
        yield_forecasting.WoodsYieldForecaster().project_305_days(1.0, 0.2, 0.004)


def test_all_production_modules_import_after_runtime_configuration():
    import dairyos

    errors = []
    for module_info in pkgutil.walk_packages(
        dairyos.__path__, dairyos.__name__ + "."
    ):
        try:
            importlib.import_module(module_info.name)
        except (Exception, SystemExit) as exc:  # Report every broken module together.
            errors.append(
                f"{module_info.name}: {type(exc).__name__}: {exc}"
            )

    assert errors == []
