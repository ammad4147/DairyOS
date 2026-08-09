from ..models.executive_alert import ExecutiveAlert


class AlertPriorityService:


    def generate(

        self,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False

    ):


        alerts = []


        if replacement_shortage:

            alerts.append(

                ExecutiveAlert(

                    category="REPLACEMENT",

                    priority=1,

                    severity_score=100,

                    issue="Replacement pipeline shortage detected",

                    recommended_action=
                    "Secure replacement animals to protect future production"

                )

            )


        if health_alerts > 0:

            alerts.append(

                ExecutiveAlert(

                    category="HEALTH",

                    priority=2,

                    severity_score=80,

                    issue="Active animal health alerts detected",

                    recommended_action=
                    "Review animal health alerts"

                )

            )


        if open_cows > 3:

            alerts.append(

                ExecutiveAlert(

                    category="REPRODUCTION",

                    priority=3,

                    severity_score=60,

                    issue="Open cow performance requires attention",

                    recommended_action=
                    "Review open cow list"

                )

            )


        alerts.sort(

            key=lambda alert: alert.priority

        )


        return alerts