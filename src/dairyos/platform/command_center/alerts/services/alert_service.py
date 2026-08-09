class AlertService:
    """
    Manages Command Center alerts.
    """



    def __init__(self):

        self.alerts = []



    def create(
        self,
        alert,
    ):

        self.alerts.append(alert)

        return alert



    def open_alerts(self):

        return [

            alert

            for alert in self.alerts

            if alert.status == "open"

        ]



    def critical_alerts(self):

        return [

            alert

            for alert in self.alerts

            if alert.severity == "critical"

        ]

