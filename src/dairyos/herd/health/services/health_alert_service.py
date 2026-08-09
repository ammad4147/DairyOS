from datetime import datetime

from ..models.health_alert import HealthAlert



class HealthAlertService:



    def __init__(self):

        self.alerts = []



    def create(

        self,

        animal_id,

        alert_type,

        severity,

        description,

        assigned_to

    ):

        alert = HealthAlert(

            animal_id,

            alert_type,

            severity,

            description,

            assigned_to,

            "OPEN",

            datetime.now()

        )


        self.alerts.append(alert)


        return alert



    def get_open_alerts(

        self

    ):

        return [

            alert

            for alert in self.alerts

            if alert.status == "OPEN"

        ]



    def close(

        self,

        alert

    ):

        alert.status = "CLOSED"

        return alert
