from ..models.escalation import Escalation



class EscalationService:



    def evaluate(

        self,

        priority_score,

        category=""

    ):


        if priority_score >= 90:

            level = "OWNER ATTENTION"

            owner = "OWNER"

            response = "7 DAYS"


        elif priority_score >= 60:

            level = "MANAGER ATTENTION"

            owner = "FARM MANAGER"

            response = "14 DAYS"


        else:

            level = "MONITOR"

            owner = "OPERATIONS TEAM"

            response = "30 DAYS"



        reason = (

            f"{category} requires {level.lower()}"

            if category

            else "Operational condition requires review"

        )



        return Escalation(

            level,

            owner,

            response,

            reason,

            priority_score

        )



    def requires_owner_attention(

        self,

        escalation

    ):


        return escalation.level == "OWNER ATTENTION"



    def sort_escalations(

        self,

        escalations

    ):


        return sorted(

            escalations,

            key=lambda x: x.priority_score,

            reverse=True

        )
