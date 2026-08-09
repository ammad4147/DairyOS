from dairyos.platform.digital_twin.persistence.models.digital_twin_snapshot import (
    DigitalTwinSnapshot,
)



class DigitalTwinRepository:
    """
    Stores digital twin historical snapshots.
    """



    def __init__(self):

        self.snapshots = []



    def save(

        self,

        farm_id,

        state,

        snapshot_type,

    ):


        snapshot = DigitalTwinSnapshot(

            farm_id=farm_id,

            state=state,

            snapshot_type=snapshot_type,

        )


        self.snapshots.append(snapshot)


        return snapshot



    def history(self):

        return self.snapshots

