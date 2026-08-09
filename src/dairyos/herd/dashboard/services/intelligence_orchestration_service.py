from ..models.intelligence_orchestration import IntelligenceOrchestration



class IntelligenceOrchestrationService:



    def coordinate(

        self,

        issue,

        action,

        confidence

    ):


        if confidence >= 75:

            status = "ATTENTION REQUIRED"

            priority = "HIGH"


        elif confidence >= 50:

            status = "MONITOR"

            priority = "MEDIUM"


        else:

            status = "STABLE"

            priority = "LOW"



        return IntelligenceOrchestration(

            status,

            issue,

            action,

            confidence,

            priority

        )
