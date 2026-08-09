"""
DairyOS Executive Intelligence Bridge

Enterprise executive presentation adapter.

Converts intelligence dashboard summaries
into executive decision models.

Does not contain intelligence logic.
"""


from dairyos.herd.dashboard.models.executive_intelligence_summary import (
    ExecutiveIntelligenceSummary,
)

from dairyos.herd.dashboard.models.executive_cockpit import (
    ExecutiveCockpit,
)

from dairyos.herd.dashboard.models.executive_command_center import (
    ExecutiveCommandCenter,
)



class ExecutiveIntelligenceBridge:
    """
    Converts intelligence summaries into
    executive dashboard representations.
    """


    def _get_governance_value(
        self,
        governance,
        field,
        default=None,
    ):

        if governance is None:

            return default


        if isinstance(
            governance,
            dict,
        ):

            return governance.get(
                field,
                default,
            )


        return getattr(
            governance,
            field,
            default,
        )



    def build_summary(
        self,
        dashboard_summary: dict,
    ):

        governance = dashboard_summary.get(
            "governance"
        )


        stages = dashboard_summary.get(
            "stages",
            [],
        )


        return ExecutiveIntelligenceSummary(

            farm_status=dashboard_summary.get(
                "status",
                "unknown",
            ),


            top_concern=self._get_governance_value(
                governance,
                "reason",
                "No concern identified",
            ),


            recommended_focus=(
                stages[0]
                if stages
                else
                "Monitor operations"
            ),


            priority_actions=[],


            owner_attention=(
                self._get_governance_value(
                    governance,
                    "approved",
                    False,
                )
                is False
            ),
        )



    def build_cockpit(
        self,
        summary: ExecutiveIntelligenceSummary,
    ):

        return ExecutiveCockpit(

            farm_name="Trident Dairies",

            overall_score=0,

            health_score=0,

            production_score=0,

            reproduction_score=0,

            financial_score=0,

            risk_level=(
                "attention"
                if summary.owner_attention
                else
                "normal"
            ),

            priority=summary.recommended_focus,

            summary=summary.top_concern,

            actions=summary.priority_actions,

            alerts=[],
        )



    def build_command_center(
        self,
        cockpit: ExecutiveCockpit,
    ):

        return ExecutiveCommandCenter(

            farm_name=cockpit.farm_name,

            overall_score=cockpit.overall_score,

            risk_level=cockpit.risk_level,

            decision_required=(
                len(cockpit.alerts) > 0
            ),

            priority_level=cockpit.priority,

            top_decision=cockpit.summary,

            recommended_action=(
                cockpit.actions[0]
                if cockpit.actions
                else "Continue monitoring"
            ),

            business_impact=(
                "Operational intelligence review"
            ),

            time_horizon="current_cycle",
        )
