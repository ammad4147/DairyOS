"""Enterprise DairyOS runtime bootstrap coordinator.

ApplicationRuntime is the sole application composition root.  This bootstrap
coordinates enterprise integration services around that already-composed
runtime; it does not construct a second application composition graph.
"""

from dairyos.application.application_runtime import ApplicationRuntime
from dairyos.platform.integration.services.platform_service_registry import (
    PlatformServiceRegistry,
)
from dairyos.platform.integration.models.platform_service import PlatformService
from dairyos.platform.runtime import PlatformRuntime
from dairyos.platform.health.services.platform_health_service import (
    PlatformHealthService,
)
from dairyos.platform.readiness.services.readiness_service import ReadinessService
from dairyos.platform.readiness.services.operational_status_gateway import (
    OperationalStatusGateway,
)
from dairyos.platform.domain_registry.services.domain_registry_service import (
    DomainRegistryService,
)
from dairyos.platform.domain_health.services.domain_health_service import (
    DomainHealthService,
)
from dairyos.platform.observability.services.observability_service import (
    ObservabilityService,
)
from dairyos.platform.events.services.event_store import EventStore
from dairyos.platform.events.services.event_bus import EventBus
from dairyos.platform.events.integration.services.event_subscriber_registry import (
    EventSubscriberRegistry,
)
from dairyos.platform.events.integration.services.event_dispatcher import (
    EventDispatcher,
)
from dairyos.platform.events.integration.services.operational_event_publisher import (
    OperationalEventPublisher,
)
from dairyos.operations.commands.services.command_dispatcher import CommandDispatcher
from dairyos.operations.commands.services.operational_command_registry import (
    OperationalCommandRegistry,
)
from dairyos.operations.tasks.services.task_dispatcher import TaskDispatcher
from dairyos.operations.tasks.services.task_registry import TaskRegistry
from dairyos.operations.tasks.integration.services.operational_task_gateway import (
    OperationalTaskGateway,
)
from dairyos.operations.workflows.integration.services.operational_workflow_runtime import (
    OperationalWorkflowRuntime,
)
from dairyos.intelligence.operations.workflow.integration.workflow_intelligence_runtime import (
    WorkflowIntelligenceRuntime,
)
from dairyos.platform.bootstrap.models.bootstrap_result import BootstrapResult


class EnterpriseRuntimeBootstrap:
    """Coordinate enterprise services around an existing ApplicationRuntime."""

    def __init__(
        self,
        application_runtime: ApplicationRuntime,
        platform_runtime: PlatformRuntime | None = None,
    ) -> None:
        self.application_runtime = application_runtime
        self.platform_runtime = platform_runtime or PlatformRuntime()
        self.registry = PlatformServiceRegistry()

        self.health_service = PlatformHealthService(container=self)
        self.readiness_service = ReadinessService()
        self.domain_registry = DomainRegistryService()
        self.domain_health_service = DomainHealthService(self.domain_registry)
        self.observability_service = ObservabilityService()

        self.event_store = EventStore(
            repository=self.application_runtime.operational_event_repository
        )
        self.event_bus = EventBus()
        self.event_subscribers = EventSubscriberRegistry()
        self.event_dispatcher = EventDispatcher(self.event_subscribers)
        self.event_publisher = OperationalEventPublisher(
            store=self.event_store,
            bus=self.event_bus,
            dispatcher=self.event_dispatcher,
        )

        self.application_runtime.farm_operations_runtime.operational_event_publisher = (
            self.event_publisher
        )
        self.application_runtime.execution_tracking_service.event_publisher = (
            self.event_publisher
        )

        self.event_subscribers.register(
            "OPERATIONAL_EXECUTION_COMPLETED",
            self.application_runtime.execution_event_subscriber.handle,
        )
        self.event_subscribers.register(
            "OPERATIONAL_EXECUTION_VERIFIED",
            self.application_runtime.execution_event_subscriber.handle,
        )

        self.command_dispatcher = CommandDispatcher()
        self.command_registry = OperationalCommandRegistry(
            dispatcher=self.command_dispatcher,
            event_publisher=self.event_publisher,
        )

        self.task_dispatcher = TaskDispatcher()
        self.task_registry = TaskRegistry(
            dispatcher=self.task_dispatcher,
            event_publisher=self.event_publisher,
        )
        self.task_gateway = OperationalTaskGateway(dispatcher=self.task_dispatcher)

        self.workflow_runtime = OperationalWorkflowRuntime(
            event_publisher=self.event_publisher,
        )
        self.workflow_intelligence_runtime = WorkflowIntelligenceRuntime()

        self.operational_status = OperationalStatusGateway(
            runtime=self.platform_runtime,
            health_service=self.health_service,
            readiness_service=self.readiness_service,
            domain_health_service=self.domain_health_service,
            observability_service=self.observability_service,
        )

    def register(self, name: str, service: object) -> None:
        self.registry.register(PlatformService(name=name, service=service))

    def register_application_services(self) -> None:
        self.register("application_runtime", self.application_runtime)
        self.register(
            "farm_operations_runtime",
            self.application_runtime.farm_operations_runtime,
        )
        self.register(
            "dashboard_builder_service",
            self.application_runtime.dashboard_builder_service,
        )

    def register_platform_services(self) -> None:
        self.register("platform_runtime", self.platform_runtime)
        self.register("platform_health_service", self.health_service)
        self.register("readiness_service", self.readiness_service)
        self.register("domain_health_service", self.domain_health_service)
        self.register("observability_service", self.observability_service)
        self.register("operational_status_gateway", self.operational_status)

    def register_event_services(self) -> None:
        self.register("operational_event_store", self.event_store)
        self.register("operational_event_bus", self.event_bus)
        self.register("event_subscriber_registry", self.event_subscribers)
        self.register("event_dispatcher", self.event_dispatcher)
        self.register("operational_event_publisher", self.event_publisher)

    def register_workflow_intelligence_events(self) -> None:
        adapter = self.workflow_intelligence_runtime.event_adapter.handle
        for event_name in ("workflow_created", "workflow_started", "workflow_completed"):
            self.event_subscribers.register(event_name, adapter)

    def register_command_services(self) -> None:
        self.register("operational_command_dispatcher", self.command_dispatcher)
        self.register("operational_command_registry", self.command_registry)

    def register_task_services(self) -> None:
        self.register("operational_task_dispatcher", self.task_dispatcher)
        self.register("operational_task_registry", self.task_registry)
        self.register("operational_task_gateway", self.task_gateway)

    def register_workflow_services(self) -> None:
        self.register("operational_workflow_runtime", self.workflow_runtime)
        self.register(
            "operational_workflow_service",
            self.workflow_runtime.workflow_service,
        )
        self.register(
            "operational_workflow_gateway",
            self.workflow_runtime.workflow_gateway,
        )
        self.register(
            "workflow_event_publisher",
            self.workflow_runtime.workflow_event_publisher,
        )

    def start(self) -> BootstrapResult:
        self.register_application_services()
        self.platform_runtime.start()
        self.register_platform_services()
        self.register_event_services()
        self.register_workflow_intelligence_events()
        self.command_registry.register_defaults()
        self.register_command_services()
        self.task_registry.register_defaults()
        self.register_task_services()
        self.register_workflow_services()

        return BootstrapResult(
            started=True,
            services_loaded=len(self.registry.active_services()),
            runtime_ready=self.platform_runtime.state.is_running(),
        )
