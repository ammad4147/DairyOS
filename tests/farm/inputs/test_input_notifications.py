from dairyos.farm.inputs.notifications.input_notification_service import (
    InputNotificationService,
)


class FakeIntelligence:

    def evaluate(self):

        class Result:

            attention_required = True

            missing_inputs = [
                "MILK_ENTRY"
            ]

        return Result()



def test_missing_operational_input_generates_notification():

    service = InputNotificationService(
        intelligence_service=FakeIntelligence()
    )


    notification = (
        service.evaluate()
    )


    assert notification is not None

    assert (
        notification.notification_type
        ==
        "missing_operational_input"
    )

    assert (
        notification.requires_attention
        is True
    )
