"""
DairyOS Intelligence Command Center API

Enterprise application boundary.

Connects:

Dashboard
    |
Command Center API
    |
Autonomous Intelligence Runtime
"""


from dairyos.intelligence.integration.autonomous_intelligence_composer import (
    AutonomousIntelligenceComposer,
)

from dairyos.intelligence.integration.intelligence_dashboard_bridge import (
    IntelligenceDashboardBridge,
)


class CommandCenterAPI:
    """
    Application boundary for intelligence command center.
    """


    def __init__(
        self,
        composer=None,
        bridge=None,
    ):

        self.composer = (
            composer
            if composer
            else AutonomousIntelligenceComposer()
        )

        self.bridge = (
            bridge
            if bridge
            else IntelligenceDashboardBridge()
        )


    def execute_cycle(
        self,
        context=None,
    ):

        result = self.composer.run(
            context
        )

        return self.bridge.build_summary(
            result
        )
