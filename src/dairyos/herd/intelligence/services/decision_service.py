from dairyos.herd.intelligence.models.herd_decision import HerdDecision



class DecisionService:



    def evaluate(

        self,

        open_cows=0,

        health_alerts=0,

        replacement_shortage=False

    ):


        recommendations = []

        risk = "LOW"

        attention = False


        if health_alerts > 0:

            attention = True

            recommendations.append(

                "Review animal health alerts"

            )


        if open_cows > 3:

            attention = True

            recommendations.append(

                "Review reproductive performance"

            )


        if replacement_shortage:

            risk = "HIGH"

            attention = True

            recommendations.append(

                "Replacement pipeline shortage detected"

            )


        elif attention:

            risk = "MEDIUM"



        return HerdDecision(

            risk_level=risk,

            attention_required=attention,

            recommendations=recommendations

        )



    def evaluate_context(

        self,

        context

    ):


        score = 0

        recommendations = []



        if getattr(context, "health_alerts", 0) > 0:

            score += 20

            recommendations.append(

                "Review animal health alerts"

            )



        if getattr(context, "open_cows", 0) > 3:

            score += 15

            recommendations.append(

                "Review reproductive performance"

            )



        if getattr(context, "replacement_shortage", False):

            score += 40

            recommendations.append(

                "Review replacement pipeline"

            )



        if getattr(context, "production_status", "") == "INACTIVE":

            score += 15

            recommendations.append(

                "Review milk production activity"

            )



        if getattr(context, "financial_status", "") == "WARNING":

            score += 10

            recommendations.append(

                "Review financial position"

            )



        if score >= 51:

            risk = "HIGH"

            priority = "URGENT"


        elif score >= 21:

            risk = "MEDIUM"

            priority = "HIGH"


        else:

            risk = "LOW"

            priority = "NORMAL"



        return HerdDecision(

            risk_level=risk,

            attention_required=(score > 0),

            recommendations=recommendations,

            priority_level=priority,

            decision_score=score

        )
