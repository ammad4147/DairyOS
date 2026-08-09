from ..models.executive_operations_cockpit import (
    ExecutiveOperationsCockpit,
)


class ExecutiveOperationsCockpitService:
    """
    Converts operational control information
    into executive management view.
    """


    def generate_cockpit(
        self,
        health_status: str = "GREEN",
        operational_score: float = 100.0,
        control_status: str = "GREEN",
    ) -> ExecutiveOperationsCockpit:


        if control_status == "RED":
            return ExecutiveOperationsCockpit(
                overall_status="RED",
                risk_level="HIGH",
                management_focus="Immediate intervention required",
                action_required=True,
                operational_score=operational_score,
            )


        if control_status == "AMBER":
            return ExecutiveOperationsCockpit(
                overall_status="AMBER",
                risk_level="MEDIUM",
                management_focus="Review operational exceptions",
                action_required=True,
                operational_score=operational_score,
            )


        return ExecutiveOperationsCockpit(
            overall_status=health_status,
            risk_level="LOW",
            management_focus="Maintain operational excellence",
            action_required=False,
            operational_score=operational_score,
        )
