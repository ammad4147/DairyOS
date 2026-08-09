from dairyos.platform.autonomy.copilot.models.copilot_response import (
    CopilotResponse,
)



class FarmCopilot:
    """
    Domain-specific dairy operations assistant.
    """



    def respond(

        self,

        question,

        recommendations=None,

    ):


        recommendations = recommendations or []


        return CopilotResponse(

            message=(

                "Farm operational review completed."

            ),

            confidence=0.0,

            recommendations=recommendations,

        )

