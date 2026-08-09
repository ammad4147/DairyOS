from dairyos.core.notifications.models import Notification
from dairyos.core.notifications.services.dispatcher import NotificationDispatcher

from dairyos.core.alerts.services.alert_engine import AlertEngine



def test_notification_dispatch():

    dispatcher = NotificationDispatcher()

    notification = Notification(
        recipient="FARM_MANAGER",
        message="Check new calf"
    )

    result = dispatcher.send(
        notification
    )

    assert result.status == "NEW"



def test_alert_creation():

    engine = AlertEngine()

    alert = engine.create_alert(
        "ANIMAL_HEALTH",
        "High temperature detected",
        "HIGH"
    )

    assert alert.priority == "HIGH"
