from dairyos.platform.command_center.farm_board.models.farm_status_snapshot import (
    FarmStatusSnapshot,
)



class FarmBoardService:
    """
    Generates farm-wide operational snapshots.
    """



    def snapshot(self):

        return FarmStatusSnapshot(

            farm_name="Trident Dairies",

            departments=[],

            metrics=[],

        )

