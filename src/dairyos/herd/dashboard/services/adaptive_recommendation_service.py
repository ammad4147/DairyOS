from ..models.adaptive_recommendation import AdaptiveRecommendation



class AdaptiveRecommendationService:



    def recommend(

        self,

        category,

        actions

    ):


        if not actions:

            return AdaptiveRecommendation(

                category,

                "No recommendation available",

                0,

                "No historical evidence"

            )


        best_action = max(

            actions,

            key=lambda x: x["success_rate"]

        )


        confidence = best_action["success_rate"]



        return AdaptiveRecommendation(

            category,

            best_action["action"],

            confidence,

            "Highest historical success rate"

        )
