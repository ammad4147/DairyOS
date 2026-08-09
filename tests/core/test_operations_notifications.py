from datetime import datetime


from dairyos.operations.notifications.models.notification import (
    Notification,
)

from dairyos.operations.notifications.models.notification_type import (
    NotificationType,
)

from dairyos.operations.notifications.services.notification_service import (
    NotificationService,
)

from dairyos.operations.notifications.services.notification_dispatch_service import (
    NotificationDispatchService,
)



def test_notification_creation():

    service = NotificationService()


    notification = Notification(
        notification_id="NOT-001",
        recipient="Farm Manager",
        message="Feed task delayed",
        notification_type=NotificationType.ALERT,
        created_at=datetime.now(),
    )


    service.create_notification(notification)


    assert len(service.pending_notifications()) == 1



def test_notification_dispatch():

    notification = Notification(
        notification_id="NOT-002",
        recipient="Supervisor",
        message="Task reminder",
        notification_type=NotificationType.REMINDER,
        created_at=datetime.now(),
    )


    service = NotificationDispatchService()


    service.dispatch(notification)


    assert notification.sent is True
