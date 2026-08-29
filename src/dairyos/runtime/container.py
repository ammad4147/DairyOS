"""Central DairyOS runtime compatibility facade.

Sprint-038 Batch 3.2-A

RuntimeContainer no longer composes a second application graph.

ApplicationRuntime is the sole composition root.

This facade exists only to preserve the established RuntimeContainer
surface while callers migrate to ApplicationRuntime directly.
"""

from dairyos.application.application_runtime import (
    ApplicationRuntime,
)


class RuntimeContainer:
    """
    Compatibility facade over ApplicationRuntime.

    No application dependencies are constructed here.

    The container delegates all composition, persistence, event
    infrastructure, operational state, intelligence, execution,
    input, decision, and dashboard services to ApplicationRuntime.
    """

    def __init__(
        self,
        milk_repo=None,
        application_runtime=None,
    ):
        self.runtime = (
            application_runtime
            if application_runtime is not None
            else ApplicationRuntime(
                milk_repository=milk_repo,
            )
        )

        self._started = False

        self.operations = None
        self.dashboard = None
        self.command_center = None

        self._expose_runtime()

    def _expose_runtime(self):
        runtime = self.runtime

        self.repository_factory = runtime.repository_factory
        self.event_journal = runtime.event_journal

        self.animal_repository = runtime.animal_repository
        self.milk_repo = runtime.milk_repository
        self.milk_repository = runtime.milk_repository
        self.feed_repository = runtime.feed_repository
        self.health_repository = runtime.health_repository
        self.breeding_repository = runtime.breeding_repository
        self.treatment_repository = runtime.treatment_repository
        self.drug_reference_repository = runtime.drug_reference_repository
        self.withdrawal_service = runtime.withdrawal_service
        self.operational_event_repository = runtime.operational_event_repository
        self.operational_state_repository = runtime.operational_state_repository
        self.operational_input_repository = runtime.operational_input_repository
        self.farm_operation_event_bus = runtime.farm_operation_event_bus
        self.lifecycle_event_bridge = runtime.lifecycle_event_bridge
        self.lifecycle_event_publisher = runtime.lifecycle_event_publisher
        self.lifecycle_engine = runtime.lifecycle_engine

        self.animal_operational_state_repository = runtime.animal_operational_state_repository
        self.animal_event_projection = runtime.animal_event_projection
        self.farm_operational_state_service = runtime.operational_state_service
        self.operational_state_service = runtime.operational_state_service
        self.operational_state_query_service = runtime.operational_state_query_service

        self.operational_input_registry = runtime.operational_input_registry
        self.input_normalization_service = runtime.input_normalization_service
        self.input_query_service = runtime.input_query_service
        self.input_analysis_service = runtime.input_analysis_service
        self.input_intelligence_service = runtime.input_intelligence_service
        self.input_notification_service = runtime.input_notification_service
        self.input_pattern_analyzer_service = runtime.input_pattern_analyzer_service
        self.input_deviation_detection_service = runtime.input_deviation_detection_service
        self.input_learning_bridge = runtime.input_learning_bridge
        self.input_governance_service = runtime.input_governance_service
        self.input_command_projection_service = runtime.input_command_projection_service
        self.input_ingestion_service = runtime.input_ingestion_service
        self.operational_input_command_service = runtime.operational_input_command_service
        self.input_gateway = runtime.input_gateway
        self.operational_input_projection_bridge = runtime.operational_input_projection_bridge

        self.farm_operations_runtime = runtime.farm_operations_runtime
        self.farm_day_runtime = runtime.farm_day_runtime
        self.operations = runtime.farm_operations_runtime

        self.animal_intelligence_service = runtime.animal_intelligence_service
        self.milk_production_intelligence_service = runtime.milk_production_intelligence_service
        self.milk_production_trend_intelligence_service = runtime.milk_production_trend_intelligence_service
        self.daily_milk_production_command_view_service = runtime.daily_milk_production_command_view_service
        self.intelligence_runtime_service = runtime.intelligence_runtime_service
        self.intelligence_query_service = runtime.intelligence_query_service
        self.intelligence_decision_bridge = runtime.intelligence_decision_bridge

        self.operational_execution_service = runtime.operational_execution_service
        self.execution_lifecycle_bridge = runtime.execution_lifecycle_bridge
        self.execution_lifecycle_event_handler = runtime.execution_lifecycle_event_handler
        self.execution_event_subscriber = runtime.execution_event_subscriber
        self.execution_tracking_service = runtime.execution_tracking_service

        self.operational_decision_service = runtime.operational_decision_service
        self.decision_ranking_service = runtime.decision_ranking_service
        self.operational_action_service = runtime.operational_action_service
        self.decision_action_bridge = runtime.decision_action_bridge
        self.decision_activation_service = runtime.decision_activation_service
        self.action_execution_bridge = runtime.action_execution_bridge
        self.closure_management_service = runtime.closure_management_service
        self.operational_learning_bridge = runtime.operational_learning_bridge

        self.operations_command_service = runtime.operations_command_service
        self.operations_health_service = runtime.operations_health_service
        self.executive_operations_service = runtime.executive_operations_service
        self.dashboard_builder_service = runtime.dashboard_builder_service
        self.dashboard_summary_service = runtime.dashboard_summary_service
        self.dashboard_projection_service = runtime.dashboard_projection_service
        self.operational_heads_up_service = runtime.operational_heads_up_service
        self.operations_timeline_service = runtime.operations_timeline_service
        self.missing_input_detection_service = runtime.missing_input_detection_service
        self.operational_command_center_service = runtime.operational_command_center_service
        self.command_center_projection_service = runtime.command_center_projection_service

    def rebuild(self):
        """Rebuild the compatibility dashboard projection from the sole runtime."""
        return self.dashboard_projection_service.project_compatibility_dashboard_from_container(self)

    def publish_event(self, event):
        self.runtime.publish_event(event)
        if self.dashboard is not None:
            self.dashboard.rebuild()

    def restore_state(self):
        self.runtime.restore_state()
        for event in self.event_journal.all_events():
            animal_id = (getattr(event, "payload", None) or {}).get("animal_id")
            if animal_id and self.animal_operational_state_repository.get(animal_id) is None:
                self.animal_event_projection.apply(event)
        if self.dashboard is not None:
            self.dashboard.rebuild()

    def health_snapshot(self):
        return self.runtime.health_snapshot()

    @property
    def started(self):
        return self._started

    @started.setter
    def started(self, value):
        self._started = bool(value)

    def start(self):
        if self._started:
            return
        self.operations = self.runtime.farm_operations_runtime
        self.dashboard = self
        self.restore_state()
        self._started = True

    def stop(self):
        self._started = False

    def shutdown(self):
        self.stop()
