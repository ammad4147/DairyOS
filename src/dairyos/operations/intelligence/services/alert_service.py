from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Alert:
    alert_id: str
    message: str
    severity: str
    created_at: datetime = datetime.utcnow()
    resolved: bool = False

class AlertService:
    def __init__(self):
        self._alerts: List[Alert] = []

    def create_alert(self, message: str, severity: str = "info") -> Alert:
        alert = Alert(alert_id=str(len(self._alerts)+1), message=message, severity=severity)
        self._alerts.append(alert)
        return alert

    def resolve_alert(self, alert_id: str) -> bool:
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                return True
        return False

    def get_unresolved(self) -> List[Alert]:
        return [a for a in self._alerts if not a.resolved]
