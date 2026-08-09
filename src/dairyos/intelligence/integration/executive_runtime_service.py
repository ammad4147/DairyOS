"""
DairyOS Executive Runtime Service

Enterprise executive runtime read boundary.

Combines:

- autonomous runtime session
- runtime intelligence metadata
- intelligence dashboard bridge
- executive intelligence bridge

Provides executive consumption view.

Does not control execution.
"""


from dairyos.intelligence.integration.intelligence_dashboard_bridge import (
    IntelligenceDashboardBridge,
)

from dairyos.intelligence.integration.executive_intelligence_bridge import (
    ExecutiveIntelligenceBridge,
)



class ExecutiveRuntimeService:
    """
    Converts autonomous runtime execution
    into executive decision representations.
    """


    def __init__(
        self,
        session=None,
        dashboard_bridge=None,
        executive_bridge=None,
    ):

        if session is None:

            from dairyos.intelligence.integration.autonomous_runtime_session import (
                AutonomousRuntimeSession,
            )

            session = AutonomousRuntimeSession()


        self.session = session


        self.dashboard_bridge = (
            dashboard_bridge
            if dashboard_bridge
            else IntelligenceDashboardBridge()
        )


        self.executive_bridge = (
            executive_bridge
            if executive_bridge
            else ExecutiveIntelligenceBridge()
        )



    def execute(
        self,
        context=None,
    ):

        runtime_session = self.session.execute(
            context
        )


        result = runtime_session.get(
            "result",
            {},
        )


        dashboard = (
            self.dashboard_bridge
            .build_summary(
                result
            )
        )


        executive_summary = (
            self.executive_bridge
            .build_summary(
                result
            )
        )


        cockpit = (
            self.executive_bridge
            .build_cockpit(
                executive_summary
            )
        )


        command_center = (
            self.executive_bridge
            .build_command_center(
                cockpit
            )
        )


        return {

            "session": runtime_session.get(
                "session"
            ),

            "runtime": result.get(
                "runtime"
            ),

            "runtime_validation": result.get(
                "runtime_validation"
            ),

            "audit": result.get(
                "audit"
            ),

            "dashboard": dashboard,

            "executive_summary": executive_summary,

            "cockpit": cockpit,

            "command_center": command_center,

        }