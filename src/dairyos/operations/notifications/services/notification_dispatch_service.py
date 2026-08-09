class NotificationDispatchService:
    """
    Handles notification delivery.
    """


    def dispatch(
        self,
        notification,
    ):

        notification.sent = True

        return notification
