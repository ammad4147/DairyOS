from ..models.herd_command import HerdCommand



class CommandDecisionService:



    def apply_decision(

        self,

        command,

        decision

    ):


        command.decision_priority = decision.priority_level

        command.decision_score = decision.decision_score

        command.recommended_actions = decision.recommendations


        if decision.attention_required:

            command.owner_attention = (

                decision.recommendations[0]

                if decision.recommendations

                else "Review herd status"

            )


        command.overall_risk = decision.risk_level


        return command
