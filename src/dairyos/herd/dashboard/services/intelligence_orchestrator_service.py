from ..models.intelligence_brief import IntelligenceBrief



class IntelligenceOrchestratorService:



    def create_brief(

        self,

        farm_name,

        issue,

        risk_level,

        escalation,

        recommendation,

        confidence

    ):


        return IntelligenceBrief(

            farm_name,

            issue,

            risk_level,

            escalation,

            recommendation,

            confidence

        )



    def determine_risk(

        self,

        priority_score

    ):


        if priority_score >= 90:

            return "CRITICAL"


        elif priority_score >= 60:

            return "HIGH"


        else:

            return "NORMAL"



    def owner_attention_required(

        self,

        escalation

    ):


        return escalation == "OWNER ATTENTION"



    def summarize(

        self,

        brief

    ):


        return (

            f"{brief.farm_name}: "

            f"{brief.issue} - "

            f"{brief.recommendation}"

        )
