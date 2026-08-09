from typing import List

from ..models.notification import Notification


class NotificationService:
    """
    Creates operational notifications.
    """


    def __init__(self):

        self.notifications: List[Notification] = []


    def create_notification(
        self,
        notification: Notification,
    ):

        self.notifications.append(notification)

        return notification


    def pending_notifications(self):

        return [
            notification
            for notification in self.notifications
            if not notification.sent
        ]
