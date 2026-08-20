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

    Read-side management projection with dynamic status aggregation
    and defensive null-safety boundaries.
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
        self.farm_command_center_service = FarmCommandCenterService()
        self.execution_accountability_query_service = ExecutionAccountabilityQueryService()
        self.governance_query_service = GovernanceQueryService()
        self.operational_control_query_service = OperationalControlQueryService()
        self.governance_attention_query_service = GovernanceAttentionQueryService()

    def _safe_build(self, service, builder_method_name: str, fallback: dict) -> dict:
        """Safely invoke a query service projection with fallback protection."""
        try:
            if hasattr(service, builder_method_name):
                res = getattr(service, builder_method_name)()
                if isinstance(res, dict):
                    return res
                if hasattr(res, "__dict__"):
                    return dict(res.__dict__)
        except Exception:
            pass
        return fallback

    def _build_intelligence_projection(self) -> dict:
        try:
            state = self.runtime.operational_state_service.get_state()
            summary = self.runtime.intelligence_query_service.get_current_intelligence(state)
            return {
                "intelligence_summary": summary,
                "intelligence_recommendations": getattr(summary, "recommendations", []),
                "intelligence_signal_count": getattr(summary, "signal_count", 0),
                "intelligence_critical_signal_count": getattr(summary, "critical_signal_count", 0),
                "intelligence_warning_signal_count": getattr(summary, "warning_signal_count", 0),
            }
        except Exception:
            return {
                "intelligence_summary": None,
                "intelligence_recommendations": [],
                "intelligence_signal_count": 0,
                "intelligence_critical_signal_count": 0,
                "intelligence_warning_signal_count": 0,
            }

    def generate_command_center(self) -> dict:
        # 1. Build Base Command Center safely
        try:
            command_center = self.farm_command_center_service.build()
            view = dict(command_center.__dict__) if hasattr(command_center, "__dict__") else {}
        except Exception:
            view = {}

        # 2. Integrate Intelligence Signals
        intel = self._build_intelligence_projection()
        view.update(intel)

        crit_signals = intel.get("intelligence_critical_signal_count", 0)
        warn_signals = intel.get("intelligence_warning_signal_count", 0)

        # 3. Dynamic Status Evaluation (Removing Hardcoded Optimism)
        if crit_signals > 0:
            operational_status = "RED"
            priority_level = "HIGH"
            risk_level = "HIGH"
            action_required = True
            management_attention_required = True
        elif warn_signals > 0:
            operational_status = "YELLOW"
            priority_level = "MEDIUM"
            risk_level = "MODERATE"
            action_required = True
            management_attention_required = True
        else:
            operational_status = "GREEN"
            priority_level = "NORMAL"
            risk_level = "LOW"
            action_required = False
            management_attention_required = False

        view.update({
            "operational_status": operational_status,
            "priority_level": priority_level,
            "active_actions": view.get("open_tasks", []),
            "performance_score": max(0.0, 100.0 - (crit_signals * 15.0) - (warn_signals * 5.0)),
            "management_attention_required": management_attention_required,
            "recommended_focus": "Address critical intelligence signals" if action_required else "Maintain operational performance",
            "executive_status": view.get("readiness_status", "READY" if not action_required else "ATTENTION"),
            "risk_level": risk_level,
            "action_required": action_required,
        })

        # 4. Defensive Accountability Projection
        acc_proj = self._safe_build(
            self.execution_accountability_query_service,
            "build_projection",
            {"execution_accountability_count": 0, "completed_execution_count": 0, "pending_execution_count": 0}
        )
        view["accountability"] = {
            "assigned": acc_proj.get("execution_accountability_count", 0),
            "completed": acc_proj.get("completed_execution_count", 0),
            "pending": acc_proj.get("pending_execution_count", 0),
        }

        # 5. Integrate Governance, Control & Attention with Fallback Safety
        view.update(self._safe_build(self.governance_query_service, "build_projection", {}))
        view.update(self._safe_build(self.operational_control_query_service, "build_projection", {}))

        att_proj = self._safe_build(
            self.governance_attention_query_service,
            "build_projection",
            {"governance_attention_required": False, "governance_attention_count": 0, "governance_attention_items": []}
        )
        view.update(att_proj)

        view["governance_attention"] = {
            "required": att_proj.get("governance_attention_required", False),
            "count": att_proj.get("governance_attention_count", 0),
            "items": att_proj.get("governance_attention_items", []),
        }

        return view
