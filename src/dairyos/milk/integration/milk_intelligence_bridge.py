from dairyos.intelligence.command.models.farm_situation import (
    FarmSituation,
)


class MilkIntelligenceBridge:
    """
    Converts milk operational snapshots
    into intelligence command situations.
    """


    def build_situation(
        self,
        snapshot,
        farm_id="FARM-001",
    ) -> FarmSituation:

        priority = "LOW"

        status = snapshot.operational_status


        if status == "WARNING":

            priority = "MEDIUM"


        if status == "CRITICAL":

            priority = "HIGH"


        return FarmSituation(

            situation_id=(
                "MILK-"
                +
                status
            ),

            farm_id=farm_id,

            status=status,

            priority=priority,

        )
