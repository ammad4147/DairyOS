from dairyos.milk.models.milk_command_snapshot import (
    MilkCommandSnapshot,
)


class MilkCommandCenterService:
    """
    Converts milk operational intelligence
    into command center information.
    """


    def build_snapshot(
        self,
        today_litres,
        expected_litres,
        health_alerts=None,
    ):

        health_alerts = (
            health_alerts
            if health_alerts
            else []
        )


        variance = 0


        if expected_litres > 0:

            variance = round(
                (
                    (
                        today_litres
                        -
                        expected_litres
                    )
                    /
                    expected_litres
                )
                * 100,
                2
            )


        status = "NORMAL"


        if variance <= -20:

            status = "WARNING"


        if variance <= -40:

            status = "CRITICAL"


        attention = []


        if status != "NORMAL":

            attention.append(
                "Milk production below expectation"
            )


        if health_alerts:

            attention.append(
                "Animal health attention required"
            )


        return MilkCommandSnapshot(

            today_litres=today_litres,

            expected_litres=expected_litres,

            variance_percentage=variance,

            operational_status=status,

            health_alerts=health_alerts,

            attention_items=attention,

        )
