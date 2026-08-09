from dairyos.application.application_runtime import (
    ApplicationRuntime,
)

from dairyos.operations.health.services.operations_health_service import (
    OperationsHealthService,
)

from dairyos.operations.command.services.operations_command_service import (
    OperationsCommandService,
)

from dairyos.farm.operations.dashboard.farm_command_center_service import (
    FarmCommandCenterService,
)

from dairyos.operations.command_center.services.execution_accountability_query_service import (
    ExecutionAccountabilityQueryService,
)

from dairyos.operations.command_center.services.governance_query_service import (
    GovernanceQueryService,
)

from dairyos.operations.command_center.services.operational_control_query_service import (
    OperationalControlQueryService,
)

from dairyos.operations.command_center.services.governance_attention_query_service import (
    GovernanceAttentionQueryService,
)


class OperationsCommandCenterOrchestrator:
    """
    Enterprise operational command center projection.

    Read-side management projection only.

    ApplicationRuntime is the supplied composition root.

    For backward compatibility, callers may omit runtime and the
    canonical ApplicationRuntime will be created.
    """

    def __init__(
        self,
        runtime: ApplicationRuntime | None = None,
    ):

        self.runtime = (
            runtime
            if runtime is not None
            else ApplicationRuntime()
        )

        self.health_service = OperationsHealthService()

        self.command_center_service = OperationsCommandService()

        self.farm_command_center_service = (
            FarmCommandCenterService()
        )

        self.execution_accountability_query_service = (
            ExecutionAccountabilityQueryService()
        )

        self.governance_query_service = (
            GovernanceQueryService()
        )

        self.operational_control_query_service = (
            OperationalControlQueryService()
        )

        self.governance_attention_query_service = (
            GovernanceAttentionQueryService()
        )

    def _build_intelligence_projection(self):

        state = (
            self.runtime
            .operational_state_service
            .get_state()
        )

        summary = (
            self.runtime
            .intelligence_query_service
            .get_current_intelligence(
                state
            )
        )

        return {

            "intelligence_summary": summary,

            "intelligence_recommendations":
                summary.recommendations,

            "intelligence_signal_count":
                summary.signal_count,

            "intelligence_critical_signal_count":
                summary.critical_signal_count,

            "intelligence_warning_signal_count":
                summary.warning_signal_count,

        }

    def generate_command_center(self):

        command_center = (
            self.farm_command_center_service
            .build()
        )

        view = (
            command_center
            .__dict__
            .copy()
        )

        view.update({

            "operational_status": "GREEN",

            "priority_level": "NORMAL",

            "active_actions":
                view.get(
                    "open_tasks",
                    [],
                ),

            "performance_score": 100.0,

            "management_attention_required": False,

            "recommended_focus":
                "Maintain operational performance",

            "executive_status":
                view.get(
                    "readiness_status",
                    "READY",
                ),

            "risk_level": "LOW",

            "action_required": False,

        })

        view.update(
            self._build_intelligence_projection()
        )

        accountability_projection = (
            self.execution_accountability_query_service
            .build_projection()
        )

        view["accountability"] = {

            "assigned":
                accountability_projection[
                    "execution_accountability_count"
                ],

            "completed":
                accountability_projection[
                    "completed_execution_count"
                ],

            "pending":
                accountability_projection[
                    "pending_execution_count"
                ],

        }

        governance_projection = (
            self.governance_query_service
            .build_projection()
        )

        view.update(
            governance_projection
        )

        control_projection = (
            self.operational_control_query_service
            .build_projection()
        )

        view.update(
            control_projection
        )

        attention_projection = (
            self.governance_attention_query_service
            .build_projection()
        )

        view.update(
            attention_projection
        )

        view["governance_attention"] = {

            "required":
                attention_projection[
                    "governance_attention_required"
                ],

            "count":
                attention_projection[
                    "governance_attention_count"
                ],

            "items":
                attention_projection[
                    "governance_attention_items"
                ],

        }

        return view
