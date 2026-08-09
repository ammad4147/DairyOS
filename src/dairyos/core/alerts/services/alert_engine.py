from ..models.alert import Alert


class AlertEngine:


    def create_alert(
        self,
        event_type,
        message,
        priority
    ):

        return Alert(
            event_type=event_type,
            message=message,
            priority=priority
        )
