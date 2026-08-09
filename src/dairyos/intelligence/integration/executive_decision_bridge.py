"""
DairyOS Executive Decision Bridge

Integration adapter between intelligence
runtime outputs and executive decision models.

Does not contain decision policy.
Uses existing executive decision structures.
"""


from dairyos.herd.dashboard.models.executive_decision import (
    ExecutiveDecision,
)



class ExecutiveDecisionBridge:
    """
    Converts executive command information
    into executive decision representation.
    """



    def build_decision(
        self,
        command_center,
    ):

        return ExecutiveDecision(

            farm_name=command_center.farm_name,

            decision_required=(
                command_center.decision_required
            ),

            priority_level=(
                command_center.priority_level
            ),

            risk_level=(
                command_center.risk_level
            ),

            recommended_action=(
                command_center.recommended_action
            ),

            business_impact=(
                command_center.business_impact
            ),

            time_horizon=(
                command_center.time_horizon
            ),
        )
