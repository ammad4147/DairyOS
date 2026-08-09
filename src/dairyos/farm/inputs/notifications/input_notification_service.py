from dairyos.farm.inputs.notifications.input_notification import (
    OperationalInputNotification,
)


class InputNotificationService:
    """
    Converts operational input intelligence
    into attention signals.
    """


    def __init__(
        self,
        intelligence_service,
    ):

        self.intelligence_service = (
            intelligence_service
        )



    def evaluate(
        self,
    ):

        intelligence = (
            self.intelligence_service
            .evaluate()
        )


        if not intelligence.attention_required:

            return None



        missing = ", ".join(
            intelligence.missing_inputs
        )


        return OperationalInputNotification(

            notification_type=
                "missing_operational_input",

            message=
                f"Missing operational inputs: {missing}",

            severity=
                "warning",

            requires_attention=
                True,

        )



    def list_notifications(
        self,
    ):

        notification = (
            self.evaluate()
        )


        if notification is None:

            return []


        return [
            notification
        ]
