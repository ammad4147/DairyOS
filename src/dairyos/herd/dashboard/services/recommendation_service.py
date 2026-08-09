from ..models.recommendation import Recommendation


class RecommendationService:


    def generate(

        self,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False,

        financial_status="POSITIVE",

        production_status="STABLE"

    ):


        recommendations = []



        if replacement_shortage:

            recommendations.append(

                Recommendation(

                    "HERD STRATEGY",

                    "Replacement pipeline shortage",

                    "Secure replacement animals to protect future production",

                    "HIGH",

                    "30 days"

                )

            )



        if health_alerts > 0:

            recommendations.append(

                Recommendation(

                    "ANIMAL HEALTH",

                    "Health alerts detected",

                    "Review animal health cases and treatment plans",

                    "HIGH",

                    "7 days"

                )

            )



        if open_cows > 3:

            recommendations.append(

                Recommendation(

                    "REPRODUCTION",

                    "High open cow count",

                    "Review breeding performance",

                    "MEDIUM",

                    "14 days"

                )

            )



        if financial_status != "POSITIVE":

            recommendations.append(

                Recommendation(

                    "FINANCE",

                    "Financial pressure detected",

                    "Review cost controls and cash position",

                    "MEDIUM",

                    "14 days"

                )

            )



        if production_status != "STABLE":

            recommendations.append(

                Recommendation(

                    "PRODUCTION",

                    "Production performance issue",

                    "Investigate milk production performance",

                    "MEDIUM",

                    "7 days"

                )

            )



        return recommendations
