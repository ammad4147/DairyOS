from ..models.executive_command_center import ExecutiveCommandCenter


class ExecutiveCommandCenterService:


    def generate(

        self,

        cockpit,

        decision

    ):


        return ExecutiveCommandCenter(

            farm_name=cockpit.farm_name,

            overall_score=cockpit.overall_score,

            risk_level=decision.risk_level,

            decision_required=decision.decision_required,

            priority_level=decision.priority_level,

            top_decision=(

                decision.recommended_action

                if decision.decision_required

                else "Maintain current operations"

            ),

            recommended_action=decision.recommended_action,

            business_impact=decision.business_impact,

            time_horizon=decision.time_horizon

        )
