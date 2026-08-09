from ..models.notification import Notification


class NotificationDispatcher:


    def __init__(self):

        self.notifications = []


    def send(
        self,
        notification: Notification
    ):

        self.notifications.append(
            notification
        )

        return notification
