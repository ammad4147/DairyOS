from ..models.monitoring_event import MonitoringEvent



class AutonomousMonitoringService:



    def detect(

        self,

        event_id,

        category,

        metric_change,

        threshold

    ):


        if metric_change >= threshold:

            severity = "HIGH"

            action = self._action(category)


        else:

            severity = "NORMAL"

            action = "Continue monitoring"



        return MonitoringEvent(

            event_id,

            category,

            f"{category} change detected",

            severity,

            action

        )



    def _action(

        self,

        category

    ):


        actions = {

            "PRODUCTION":

                "Review production factors",

            "HEALTH":

                "Review animal health status",

            "REPRODUCTION":

                "Review breeding performance",

            "FINANCE":

                "Review financial indicators"

        }


        return actions.get(

            category,

            "Review farm condition"

        )



    def requires_attention(

        self,

        event

    ):


        return event.severity == "HIGH"
