from dairyos.farm.operations.dashboard.milk_health_summary import (
    MilkHealthSummary,
)


class MilkHealthSummaryService:
    """
    Builds milk intelligence summary
    for management dashboards.

    Currently operates as a read-side boundary.
    Future integrations may connect:
    Milk Intelligence -> this service.
    """


    def build(
        self,
        anomalies=None,
    ) -> MilkHealthSummary:

        anomalies = anomalies or []

        recommended_checks = []

        risk_count = 0


        for anomaly in anomalies:

            if anomaly.get(
                "severity",
                "LOW"
            ).upper() in [
                "MEDIUM",
                "HIGH",
            ]:

                risk_count += 1


            checks = anomaly.get(
                "recommended_checks",
                []
            )

            for check in checks:

                if check not in recommended_checks:

                    recommended_checks.append(
                        check
                    )


        return MilkHealthSummary(

            milk_anomalies=len(
                anomalies
            ),

            milk_health_risks=risk_count,

            recommended_checks=(
                recommended_checks
            ),
        )
