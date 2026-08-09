from ..models.intelligent_alert import IntelligentAlert



class AlertIntelligenceService:



    def generate_alert(

        self,

        category,

        issue,

        severity="LOW"

    ):


        if severity == "HIGH":

            urgency = "IMMEDIATE"

            score = 90


        elif severity == "MEDIUM":

            urgency = "ATTENTION"

            score = 60


        else:

            urgency = "MONITOR"

            score = 30



        action_map = {

            "HEALTH": "Review animal health alerts",

            "REPRODUCTION": "Review breeding performance",

            "HERD STRATEGY": "Review replacement pipeline",

            "PRODUCTION": "Review production performance",

            "FINANCE": "Review financial indicators"

        }



        action = action_map.get(

            category,

            "Review farm condition"

        )



        return IntelligentAlert(

            category,

            issue,

            severity,

            urgency,

            score,

            action

        )



    def rank_alerts(

        self,

        alerts

    ):


        return sorted(

            alerts,

            key=lambda x: x.priority_score,

            reverse=True

        )



    def highest_priority(

        self,

        alerts

    ):


        ranked = self.rank_alerts(alerts)


        if not ranked:

            return None


        return ranked[0]
