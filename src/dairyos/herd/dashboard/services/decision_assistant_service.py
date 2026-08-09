from ..models.decision_assistant import DecisionAssistant



class DecisionAssistantService:



    def advise(

        self,

        situation,

        recommendation,

        confidence

    ):


        if confidence >= 75:

            priority = "HIGH"

        elif confidence >= 50:

            priority = "MEDIUM"

        else:

            priority = "LOW"



        return DecisionAssistant(

            situation,

            recommendation,

            confidence,

            priority,

            "Based on highest available intelligence confidence"

        )
