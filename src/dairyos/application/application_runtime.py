"""
Application Runtime
===================

Single composition root for DairyOS.

ApplicationRuntime owns dependency wiring only.
Business logic belongs to domain/application services.

Sprint-038 Batch 3.2-A:
Runtime composition consolidation.

Persistence selection is delegated to RepositoryFactory
where stable repository contracts already exist.

RuntimeContainer is now a compatibility facade over this
runtime and must not construct a second application graph.
"""

from __future__ import annotations

from dairyos.data.repositories.repository_factory import (
    RepositoryFactory,
)

from dairyos.dashboard.services.dashboard_projection_service import (
    DashboardProjectionService,
)

from dairyos.storage.database import initialize_database

from dairyos.runtime.persistent_event_journal import (
    PersistentEventJournal,
)

from dairyos.farm.operations.repositories.adapters import (
    MemoryBreedingRepository,
)

from dairyos.farm.operations.runtime import (
    FarmOperationsRuntime,
)

from dairyos.farm.operations.events.farm_operation_event_bus import (
    FarmOperationEventBus,
)

from dairyos.farm.operations.events.operational_state_event_subscriber import (
    OperationalStateEventSubscriber,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.services.operational_state_query_service import (
    OperationalStateQueryService,
)

from dairyos.farm.herd.services.animal_event_projection import (
    AnimalEventProjection,
)

from dairyos.farm.herd.services.animal_operational_event_subscriber import (
    AnimalOperationalEventSubscriber,
)

from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)

from dairyos.farm.herd.services.animal_intelligence_service import (
    AnimalIntelligenceService,
)

from dairyos.herd.lifecycle.services.lifecycle_event_publisher import (
    LifecycleEventPublisher,
)

from dairyos.herd.lifecycle.services.lifecycle_engine import (
    LifecycleEngine,
)

from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from dairyos.operations.execution.services.execution_tracking_service import (
    ExecutionTrackingService,
)

from dairyos.operations.execution.services.execution_lifecycle_event_handler import (
    ExecutionLifecycleEventHandler,
)

from dairyos.operations.execution.services.execution_event_subscriber import (
    ExecutionEventSubscriber,
)

from dairyos.operations.execution.services.execution_lifecycle_bridge import (
    ExecutionLifecycleBridge,
)

from dairyos.intelligence.services.intelligence_runtime_service import (
    IntelligenceRuntimeService,
)

from dairyos.intelligence.services.intelligence_query_service import (
    IntelligenceQueryService,
)

from dairyos.farm.day.runtime.farm_day_runtime import (
    FarmDayRuntime,
)

from dairyos.application.identity.repositories.adapters.memory_user_repository import (
    MemoryUserRepository,
)

from dairyos.operations.command.services.operations_command_service import (
    OperationsCommandService,
)

from dairyos.operations.health.services.operations_health_service import (
    OperationsHealthService,
)

from dairyos.operations.executive.services.executive_operations_service import (
    ExecutiveOperationsService,
)

from dairyos.operations.dashboard.services.dashboard_builder_service import (
    DashboardBuilderService,
)

from dairyos.operations.dashboard.services.dashboard_summary_service import (
    DashboardSummaryService,
)

from dairyos.farm.operations.alerts.operational_heads_up_service import (
    OperationalHeadsUpService,
)

from dairyos.farm.operations.services.operations_timeline_service import (
    OperationsTimelineService,
)

from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)

from dairyos.farm.operations.services.milk_production_intelligence_service import (
    MilkProductionIntelligenceService,
)

from dairyos.farm.operations.services.daily_milk_production_command_view_service import (
    DailyMilkProductionCommandViewService,
)

from dairyos.intelligence.decision.services.intelligence_decision_bridge import (
    IntelligenceDecisionBridge,
)

from dairyos.farm.herd.services.lifecycle_event_bridge import (
    LifecycleEventBridge,
)

# ---------------------------------------------------------------------------
# Operational input subsystem
# ---------------------------------------------------------------------------

from dairyos.farm.inputs.services.input_registry import (
    OperationalInputRegistry,
)

from dairyos.farm.inputs.services.input_normalization_service import (
    InputNormalizationService,
)

from dairyos.farm.inputs.services.input_catalog import (
    InputCatalog,
)

from dairyos.farm.inputs.services.input_ingestion_service import (
    InputIngestionService,
)

from dairyos.farm.inputs.services.operational_input_projection_bridge import (
    OperationalInputProjectionBridge,
)

from dairyos.farm.inputs.learning.input_pattern_analyzer_service import (
    InputPatternAnalyzerService,
)

from dairyos.farm.inputs.analytics.input_analysis_service import (
    InputAnalysisService,
)

from dairyos.farm.inputs.intelligence.input_intelligence_service import (
    InputIntelligenceService,
)

from dairyos.farm.inputs.notifications.input_notification_service import (
    InputNotificationService,
)

from dairyos.farm.inputs.repository.operational_input_repository import (
    OperationalInputRepository,
)

from dairyos.farm.inputs.services.input_query_service import (
    InputQueryService,
)

from dairyos.farm.inputs.learning.input_deviation_detection_service import (
    InputDeviationDetectionService,
)

from dairyos.farm.inputs.learning.input_learning_bridge import (
    InputLearningBridge,
)

from dairyos.farm.inputs.governance.input_governance_service import (
    InputGovernanceService,
)

from dairyos.farm.inputs.command.input_command_projection_service import (
    InputCommandProjectionService,
)

from dairyos.farm.inputs.services.input_command_service import (
    OperationalInputCommandService,
)

from dairyos.farm.inputs.services.farm_input_gateway import (
    FarmInputGateway,
)

# ---------------------------------------------------------------------------
# Decision / command-center subsystem
# ---------------------------------------------------------------------------

from dairyos.farm.operations.state.operational_decision_service import (
    OperationalDecisionService,
)

from dairyos.operations.decisions.services.decision_ranking_service import (
    DecisionRankingService,
)

from dairyos.operations.actions.services.operational_action_service import (
    OperationalActionService,
)

from dairyos.operations.decisions.services.decision_action_bridge import (
    DecisionActionBridge,
)

from dairyos.operations.decisions.services.decision_activation_service import (
    DecisionActivationService,
)

from dairyos.operations.integration.services.action_execution_bridge import (
    ActionExecutionBridge,
)

from dairyos.operations.closure.services.closure_management_service import (
    ClosureManagementService,
)

from dairyos.operations.learning.services.operational_learning_bridge import (
    OperationalLearningBridge,
)

from dairyos.farm.command_center.services.missing_input_detection_service import (
    MissingInputDetectionService,
)

from dairyos.farm.command_center.services.operational_command_center_service import (
    OperationalCommandCenterService,
)

from dairyos.farm.command_center.services.command_center_projection_service import (
    CommandCenterProjectionService,
)

from dairyos.farm.command_center.services.attention_queue_service import (
    AttentionQueueService,
)


class ApplicationRuntime:
    """
    Single DairyOS application composition root.

    Responsibilities:

    - repository composition
    - event infrastructure composition
    - service composition
    - dependency wiring
    - runtime recovery orchestration

    No business logic belongs here.
    """

    def __init__(
        self,
        repository_factory=None,
        animal_repository=None,
        milk_repository=None,
        feed_repository=None,
        health_repository=None,
        breeding_repository=None,
        operational_event_repository=None,
        operational_state_repository=None,
        user_repository=None,
        operational_input_repository=None,
        animal_operational_state_repository=None,
        operations_command_service=None,
        operations_health_service=None,
        executive_operations_service=None,
        dashboard_builder_service=None,
        dashboard_summary_service=None,
        farm_operations_runtime=None,
        farm_day_runtime=None,
        animal_event_projection=None,
        animal_intelligence_service=None,
        lifecycle_event_publisher=None,
        lifecycle_engine=None,
        operational_execution_service=None,
        execution_lifecycle_event_handler=None,
        execution_event_subscriber=None,
        execution_tracking_service=None,
        operational_state_service=None,
        operational_state_query_service=None,
        farm_operation_event_bus=None,
        operational_heads_up_service=None,
        operations_timeline_service=None,
        milk_production_intelligence_service=None,
        milk_production_trend_intelligence_service=None,
        daily_milk_production_command_view_service=None,
        intelligence_runtime_service=None,
        intelligence_query_service=None,
        intelligence_decision_bridge=None,
        event_journal=None,
        lifecycle_event_bridge=None,
    ):

        # ------------------------------------------------------------------
        # Database / persistence boundary
        # ------------------------------------------------------------------

        initialize_database()

        self._repository_factory = (
            repository_factory
            if repository_factory is not None
            else RepositoryFactory.create()
        )

        self._animal_repository = (
            animal_repository
            if animal_repository is not None
            else self._repository_factory.animal()
        )

        self._operational_event_repository = (
            operational_event_repository
            if operational_event_repository is not None
            else self._repository_factory.operational_events()
        )

        self._operational_state_repository = (
            operational_state_repository
            if operational_state_repository is not None
            else self._repository_factory.operational_state()
        )

        self._milk_repository = (
            milk_repository
            if milk_repository is not None
            else MemoryMilkRepository()
        )

        self._feed_repository = (
            feed_repository
            if feed_repository is not None
            else MemoryFeedRepository()
        )

        self._health_repository = (
            health_repository
            if health_repository is not None
            else MemoryHealthRepository()
        )

        self._breeding_repository = (
            breeding_repository
            if breeding_repository is not None
            else self._repository_factory.breeding()
        )

        self._user_repository = (
            user_repository
            if user_repository is not None
            else MemoryUserRepository()
        )

        self._operational_input_repository = (
            operational_input_repository
            if operational_input_repository is not None
            else OperationalInputRepository()
        )

        self._event_journal = (
            event_journal
            if event_journal is not None
            else PersistentEventJournal()
        )

        # ------------------------------------------------------------------
        # Animal operational projection
        # ------------------------------------------------------------------

        self._animal_operational_state_repository = (
            animal_operational_state_repository
            if animal_operational_state_repository is not None
            else AnimalOperationalStateRepository()
        )

        self._animal_event_projection = (
            animal_event_projection
            if animal_event_projection is not None
            else AnimalEventProjection(
                repository=self._animal_operational_state_repository
            )
        )

        # ------------------------------------------------------------------
        # Operational state
        # ------------------------------------------------------------------

        self._operational_state_service = (
            operational_state_service
            if operational_state_service is not None
            else FarmOperationalStateService(
                repository=self._operational_state_repository,
                animal_projection=self._animal_event_projection,
            )
        )

        self._farm_operation_event_bus = (
            farm_operation_event_bus
            if farm_operation_event_bus is not None
            else FarmOperationEventBus()
        )

        self._operational_state_event_subscriber = (
            OperationalStateEventSubscriber(
                self._operational_state_service
            )
        )

        self._animal_operational_event_subscriber = (
            AnimalOperationalEventSubscriber(
                projection=self._animal_event_projection
            )
        )

        self._farm_operation_event_bus.subscribe(
            self._operational_state_event_subscriber
        )

        self._farm_operation_event_bus.subscribe(
            self._animal_operational_event_subscriber
        )

        # ------------------------------------------------------------------
        # Operational input subsystem
        # ------------------------------------------------------------------

        self._operational_input_registry = (
            OperationalInputRegistry()
        )

        self._input_normalization_service = (
            InputNormalizationService(
                registry=self._operational_input_registry
            )
        )

        self._input_query_service = (
            InputQueryService(
                repository=self._operational_input_repository
            )
        )

        self._input_analysis_service = (
            InputAnalysisService(
                repository=self._operational_input_repository,
                registry=self._operational_input_registry,
            )
        )

        self._input_intelligence_service = (
            InputIntelligenceService(
                analysis_service=self._input_analysis_service,
            )
        )

        self._input_notification_service = (
            InputNotificationService(
                intelligence_service=self._input_intelligence_service,
            )
        )

        self._input_pattern_analyzer_service = (
            InputPatternAnalyzerService(
                repository=self._operational_input_repository,
            )
        )

        self._input_deviation_detection_service = (
            InputDeviationDetectionService()
        )

        self._input_learning_bridge = (
            InputLearningBridge(
                pattern_service=self._input_pattern_analyzer_service,
                deviation_service=self._input_deviation_detection_service,
            )
        )

        for definition in InputCatalog.definitions():
            self._operational_input_registry.register(
                definition
            )

        self._input_governance_service = (
            InputGovernanceService()
        )

        self._input_command_projection_service = (
            InputCommandProjectionService(
                query_service=self._input_query_service,
                intelligence_service=self._input_intelligence_service,
                notification_service=self._input_notification_service,
                governance_service=self._input_governance_service,
            )
        )

        self._operational_input_projection_bridge = (
            OperationalInputProjectionBridge(
                state_service=self._operational_state_service
            )
        )

        self._input_ingestion_service = (
            InputIngestionService(
                registry=self._operational_input_registry,
                event_publisher=self.publish_event,
                repository=self._operational_input_repository,
                governance_service=self._input_governance_service,
                normalization_service=self._input_normalization_service,
            )
        )

        self._operational_input_command_service = (
            OperationalInputCommandService(
                ingestion_service=self._input_ingestion_service,
            )
        )

        self._input_gateway = (
            FarmInputGateway(
                command_service=self._operational_input_command_service,
            )
        )

        # ------------------------------------------------------------------
        # Execution infrastructure
        # ------------------------------------------------------------------

        self._operational_execution_service = (
            operational_execution_service
            if operational_execution_service is not None
            else OperationalExecutionService(
                event_journal=self._event_journal
            )
        )

        self._execution_lifecycle_bridge = (
            ExecutionLifecycleBridge()
        )

        self._execution_lifecycle_event_handler = (
            execution_lifecycle_event_handler
            if execution_lifecycle_event_handler is not None
            else ExecutionLifecycleEventHandler(
                execution_service=self._operational_execution_service,
                lifecycle_bridge=self._execution_lifecycle_bridge,
            )
        )

        self._execution_event_subscriber = (
            execution_event_subscriber
            if execution_event_subscriber is not None
            else ExecutionEventSubscriber(
                handler=self._execution_lifecycle_event_handler
            )
        )

        self._execution_tracking_service = (
            execution_tracking_service
            if execution_tracking_service is not None
            else ExecutionTrackingService(
                event_publisher=self._farm_operation_event_bus
            )
        )

        self._farm_operation_event_bus.subscribe(
            self._execution_event_subscriber
        )

        # ------------------------------------------------------------------
        # Lifecycle
        # ------------------------------------------------------------------

        self._lifecycle_event_publisher = (
            lifecycle_event_publisher
            if lifecycle_event_publisher is not None
            else LifecycleEventPublisher(
                event_bus=self._farm_operation_event_bus
            )
        )

        self._lifecycle_engine = (
            lifecycle_engine
            if lifecycle_engine is not None
            else LifecycleEngine(
                event_publisher=self._lifecycle_event_publisher
            )
        )

        self._lifecycle_event_bridge = (
            lifecycle_event_bridge
            if lifecycle_event_bridge is not None
            else LifecycleEventBridge()
        )

        # ------------------------------------------------------------------
        # Farm operations
        # ------------------------------------------------------------------

        self._farm_operations_runtime = (
            farm_operations_runtime
            if farm_operations_runtime is not None
            else FarmOperationsRuntime(
                milk_repository=self._milk_repository,
                feed_repository=self._feed_repository,
                health_repository=self._health_repository,
                breeding_repository=self._breeding_repository,
                event_repository=self._operational_event_repository,
                event_bus=self._farm_operation_event_bus,
            )
        )

        # ------------------------------------------------------------------
        # Intelligence
        # ------------------------------------------------------------------

        self._milk_production_intelligence_service = (
            milk_production_intelligence_service
            if milk_production_intelligence_service is not None
            else MilkProductionIntelligenceService(
                self._operational_state_service
            )
        )

        self._milk_production_trend_intelligence_service = (
            milk_production_trend_intelligence_service
            if milk_production_trend_intelligence_service is not None
            else MilkProductionTrendIntelligenceService(
                self._milk_production_intelligence_service
            )
        )

        self._daily_milk_production_command_view_service = (
            daily_milk_production_command_view_service
            if daily_milk_production_command_view_service is not None
            else DailyMilkProductionCommandViewService(
                self._milk_production_intelligence_service,
                self._milk_production_trend_intelligence_service,
            )
        )

        self._operational_state_query_service = (
            operational_state_query_service
            if operational_state_query_service is not None
            else OperationalStateQueryService(
                self._operational_state_service,
                milk_production_intelligence_service=(
                    self._milk_production_intelligence_service
                ),
            )
        )

        self._animal_intelligence_service = (
            animal_intelligence_service
            if animal_intelligence_service is not None
            else AnimalIntelligenceService()
        )

        self._intelligence_runtime_service = (
            intelligence_runtime_service
            if intelligence_runtime_service is not None
            else IntelligenceRuntimeService()
        )

        self._intelligence_query_service = (
            intelligence_query_service
            if intelligence_query_service is not None
            else IntelligenceQueryService(
                self._intelligence_runtime_service
            )
        )

        self._intelligence_decision_bridge = (
            intelligence_decision_bridge
            if intelligence_decision_bridge is not None
            else IntelligenceDecisionBridge()
        )

        # ------------------------------------------------------------------
        # Farm day
        # ------------------------------------------------------------------

        self._farm_day_runtime = (
            farm_day_runtime
            if farm_day_runtime is not None
            else FarmDayRuntime(
                farm_id="TRIDENT-DAIRIES",
                operations_runtime=self._farm_operations_runtime,
            )
        )

        # ------------------------------------------------------------------
        # Decision / action / closure / learning
        # ------------------------------------------------------------------

        self._operational_decision_service = (
            OperationalDecisionService(
                operational_state_service=self._operational_state_service
            )
        )

        self._decision_ranking_service = (
            DecisionRankingService()
        )

        self._operational_action_service = (
            OperationalActionService()
        )

        self._decision_action_bridge = (
            DecisionActionBridge(
                action_service=self._operational_action_service,
                execution_service=self._operational_execution_service,
            )
        )

        self._decision_activation_service = (
            DecisionActivationService(
                decision_action_bridge=self._decision_action_bridge
            )
        )

        self._action_execution_bridge = (
            ActionExecutionBridge(
                execution_service=self._operational_execution_service
            )
        )

        self._closure_management_service = (
            ClosureManagementService()
        )

        self._operational_learning_bridge = (
            OperationalLearningBridge()
        )

        # ------------------------------------------------------------------
        # Operations / dashboard
        # ------------------------------------------------------------------

        self._operations_command_service = (
            operations_command_service
            if operations_command_service is not None
            else OperationsCommandService()
        )

        self._operations_health_service = (
            operations_health_service
            if operations_health_service is not None
            else OperationsHealthService()
        )

        self._executive_operations_service = (
            executive_operations_service
            if executive_operations_service is not None
            else ExecutiveOperationsService(
                command_service=self._operations_command_service
            )
        )

        self._dashboard_projection_service = (
            DashboardProjectionService()
        )

        self._dashboard_builder_service = (
            dashboard_builder_service
            if dashboard_builder_service is not None
            else DashboardBuilderService()
        )

        self._dashboard_summary_service = (
            dashboard_summary_service
            if dashboard_summary_service is not None
            else DashboardSummaryService()
        )

        self._operational_heads_up_service = (
            operational_heads_up_service
            if operational_heads_up_service is not None
            else OperationalHeadsUpService()
        )

        self._operations_timeline_service = (
            operations_timeline_service
            if operations_timeline_service is not None
            else OperationsTimelineService()
        )

        self._missing_input_detection_service = (
            MissingInputDetectionService()
        )

        self._operational_command_center_service = (
            OperationalCommandCenterService(
                operational_state_service=self._operational_state_service,
                operations_health_service=self._operations_health_service,
                attention_queue_service=AttentionQueueService(
                    missing_input_detection_service=(
                        self._missing_input_detection_service
                    ),
                ),
            )
        )

        self._command_center_projection_service = (
            CommandCenterProjectionService()
        )

    # ======================================================================
    # Event / recovery
    # ======================================================================

    def publish_event(self, event):
        """
        Persist and distribute an event through the single runtime graph.
        """

        self._event_journal.append(event)

        self._farm_operational_event_dispatch(event)

    def _farm_operational_event_dispatch(self, event):
        self._operational_state_service.handle(event)

        self._operational_input_projection_bridge.project(event)

    def restore_state(self):
        """
        Rebuild runtime projections from the persistent event journal.
        """

        self._animal_operational_event_subscriber.projection = (
            self._animal_event_projection
        )

        for event in self._event_journal.all_events():

            self._operational_state_service.handle(event)

            self._operational_input_projection_bridge.project(event)

            if getattr(event, "name", None) != "lifecycle_changed":
                continue

            from datetime import datetime, UTC

            timestamp = event.payload.get("timestamp")

            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)

            if timestamp is None:
                timestamp = datetime.now(UTC)

            lifecycle_event = type(
                "LifecycleReplayEvent",
                (),
                {
                    "event_type": event.name,
                    "animal_id": event.payload.get("animal_id"),
                    "previous_status": event.payload.get(
                        "previous_status"
                    ),
                    "new_status": event.payload.get(
                        "new_status"
                    ),
                    "location": event.payload.get(
                        "location"
                    ),
                    "timestamp": timestamp,
                },
            )()

            farm_event = self._lifecycle_event_bridge.convert(
                lifecycle_event
            )

            self._farm_operation_event_bus.publish(
                farm_event
            )

    # ======================================================================
    # Persistence
    # ======================================================================

    @property
    def repository_factory(self):
        return self._repository_factory

    @property
    def event_journal(self):
        return self._event_journal

    # ======================================================================
    # Event infrastructure
    # ======================================================================

    @property
    def farm_operation_event_bus(self):
        return self._farm_operation_event_bus

    @property
    def lifecycle_event_bridge(self):
        return self._lifecycle_event_bridge

    @property
    def lifecycle_event_publisher(self):
        return self._lifecycle_event_publisher

    @property
    def lifecycle_engine(self):
        return self._lifecycle_engine

    # ======================================================================
    # Operational state
    # ======================================================================

    @property
    def operational_state_service(self):
        return self._operational_state_service

    @property
    def operational_state_repository(self):
        return self._operational_state_repository

    @property
    def operational_state_query_service(self):
        return self._operational_state_query_service

    # ======================================================================
    # Farm operations
    # ======================================================================

    @property
    def farm_operations_runtime(self):
        return self._farm_operations_runtime

    @property
    def farm_day_runtime(self):
        return self._farm_day_runtime

    @property
    def animal_repository(self):
        return self._animal_repository

    @property
    def milk_repository(self):
        return self._milk_repository

    @property
    def feed_repository(self):
        return self._feed_repository

    @property
    def health_repository(self):
        return self._health_repository

    @property
    def breeding_repository(self):
        return self._breeding_repository

    @property
    def operational_event_repository(self):
        return self._operational_event_repository

    # ======================================================================
    # Animal
    # ======================================================================

    @property
    def animal_operational_state_repository(self):
        return self._animal_operational_state_repository

    @property
    def animal_event_projection(self):
        return self._animal_event_projection

    @property
    def animal_intelligence_service(self):
        return self._animal_intelligence_service

    # ======================================================================
    # Identity
    # ======================================================================

    @property
    def user_repository(self):
        return self._user_repository

    # ======================================================================
    # Input subsystem
    # ======================================================================

    @property
    def operational_input_registry(self):
        return self._operational_input_registry

    @property
    def operational_input_repository(self):
        return self._operational_input_repository

    @property
    def input_normalization_service(self):
        return self._input_normalization_service

    @property
    def input_query_service(self):
        return self._input_query_service

    @property
    def input_analysis_service(self):
        return self._input_analysis_service

    @property
    def input_intelligence_service(self):
        return self._input_intelligence_service

    @property
    def input_notification_service(self):
        return self._input_notification_service

    @property
    def input_pattern_analyzer_service(self):
        return self._input_pattern_analyzer_service

    @property
    def input_deviation_detection_service(self):
        return self._input_deviation_detection_service

    @property
    def input_learning_bridge(self):
        return self._input_learning_bridge

    @property
    def input_governance_service(self):
        return self._input_governance_service

    @property
    def input_command_projection_service(self):
        return self._input_command_projection_service

    @property
    def input_ingestion_service(self):
        return self._input_ingestion_service

    @property
    def operational_input_command_service(self):
        return self._operational_input_command_service

    @property
    def input_gateway(self):
        return self._input_gateway

    @property
    def operational_input_projection_bridge(self):
        return self._operational_input_projection_bridge

    # ======================================================================
    # Operations / dashboard
    # ======================================================================

    @property
    def operations_command_service(self):
        return self._operations_command_service

    @property
    def operations_health_service(self):
        return self._operations_health_service

    @property
    def executive_operations_service(self):
        return self._executive_operations_service

    @property
    def dashboard_projection_service(self):
        return self._dashboard_projection_service

    @property
    def dashboard_builder_service(self):
        return self._dashboard_builder_service

    @property
    def dashboard_summary_service(self):
        return self._dashboard_summary_service

    @property
    def operational_heads_up_service(self):
        return self._operational_heads_up_service

    @property
    def operations_timeline_service(self):
        return self._operations_timeline_service

    @property
    def operational_command_center_service(self):
        return self._operational_command_center_service

    @property
    def command_center_projection_service(self):
        return self._command_center_projection_service

    # ======================================================================
    # Milk intelligence
    # ======================================================================

    @property
    def milk_production_intelligence_service(self):
        return self._milk_production_intelligence_service

    @property
    def milk_production_trend_intelligence_service(self):
        return self._milk_production_trend_intelligence_service

    @property
    def daily_milk_production_command_view_service(self):
        return self._daily_milk_production_command_view_service

    # ======================================================================
    # Intelligence
    # ======================================================================

    @property
    def intelligence_runtime_service(self):
        return self._intelligence_runtime_service

    @property
    def intelligence_query_service(self):
        return self._intelligence_query_service

    @property
    def intelligence_decision_bridge(self):
        return self._intelligence_decision_bridge

    # ======================================================================
    # Execution
    # ======================================================================

    @property
    def operational_execution_service(self):
        return self._operational_execution_service

    @property
    def execution_lifecycle_bridge(self):
        return self._execution_lifecycle_bridge

    @property
    def execution_lifecycle_event_handler(self):
        return self._execution_lifecycle_event_handler

    @property
    def execution_event_subscriber(self):
        return self._execution_event_subscriber

    @property
    def execution_tracking_service(self):
        return self._execution_tracking_service

    # ======================================================================
    # Decisions / actions
    # ======================================================================

    @property
    def operational_decision_service(self):
        return self._operational_decision_service

    @property
    def decision_ranking_service(self):
        return self._decision_ranking_service

    @property
    def operational_action_service(self):
        return self._operational_action_service

    @property
    def decision_action_bridge(self):
        return self._decision_action_bridge

    @property
    def decision_activation_service(self):
        return self._decision_activation_service

    @property
    def action_execution_bridge(self):
        return self._action_execution_bridge

    @property
    def closure_management_service(self):
        return self._closure_management_service

    @property
    def operational_learning_bridge(self):
        return self._operational_learning_bridge

    @property
    def missing_input_detection_service(self):
        return self._missing_input_detection_service

    # ======================================================================
    # Compatibility health API
    # ======================================================================

    def health_snapshot(self):
        snapshot = (
            self._operations_health_service
            .generate_snapshot()
        )

        return {
            "health_status": snapshot.health_status,
            "operational_score": snapshot.operational_score,
            "active_decisions": snapshot.active_decisions,
            "pending_actions": snapshot.pending_actions,
            "tracked_outcomes": snapshot.tracked_outcomes,
            "learning_signals": snapshot.learning_signals,
            "owner_attention_required": snapshot.owner_attention_required,
        }

