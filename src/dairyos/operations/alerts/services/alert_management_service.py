from typing import List

from ..models.operational_alert import OperationalAlert


class AlertManagementService:
    """
    Creates and manages operational alerts.
    """


    def __init__(self):

        self.alerts: List[OperationalAlert] = []


    def create_alert(
        self,
        alert: OperationalAlert,
    ):

        self.alerts.append(alert)

        return alert


    def active_alerts(self):

        return [
            alert
            for alert in self.alerts
            if not alert.resolved
        ]
