from dairyos.platform.notification.models.notification import Notification
from dairyos.platform.notification.models.notification_status import NotificationStatus


class NotificationService:

    def __init__(self):
        self.notifications = []

    def create(self, notification: Notification):

        notification.status = NotificationStatus.CREATED

        self.notifications.append(notification)

        return notification


    def queue(self, notification: Notification):

        notification.status = NotificationStatus.QUEUED

        return notification


    def mark_sent(self, notification: Notification):

        notification.status = NotificationStatus.SENT

        return notification


    def acknowledge(self, notification: Notification):

        notification.status = NotificationStatus.ACKNOWLEDGED

        return notification


    def history(self):

        return self.notifications
