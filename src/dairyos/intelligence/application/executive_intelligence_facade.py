"""
DairyOS Executive Intelligence Facade

Enterprise application boundary
for executive intelligence consumers.

Coordinates executive runtime,
decision and reporting views.

Contains no intelligence logic.
"""


from dairyos.intelligence.integration.executive_runtime_service import (
    ExecutiveRuntimeService,
)

from dairyos.intelligence.integration.executive_reporting_bridge import (
    ExecutiveReportingBridge,
)

from dairyos.intelligence.integration.executive_decision_bridge import (
    ExecutiveDecisionBridge,
)



class ExecutiveIntelligenceFacade:
    """
    Unified executive intelligence access boundary.
    """



    def __init__(
        self,
        runtime_service=None,
        reporting_bridge=None,
        decision_bridge=None,
    ):


        self.runtime_service = (
            runtime_service
            if runtime_service
            else ExecutiveRuntimeService()
        )


        self.reporting_bridge = (
            reporting_bridge
            if reporting_bridge
            else ExecutiveReportingBridge()
        )


        self.decision_bridge = (
            decision_bridge
            if decision_bridge
            else ExecutiveDecisionBridge()
        )



    def execute(
        self,
        context=None,
    ):


        runtime = (
            self.runtime_service
            .execute(
                context
            )
        )


        cockpit = runtime.get(
            "cockpit"
        )


        command_center = runtime.get(
            "command_center"
        )


        return {

            "runtime": runtime,

            "decision": (
                self.decision_bridge
                .build_decision(
                    command_center
                )
                if command_center
                else None
            ),

            "report": (
                self.reporting_bridge
                .build_report(
                    cockpit
                )
                if cockpit
                else None
            ),
        }
