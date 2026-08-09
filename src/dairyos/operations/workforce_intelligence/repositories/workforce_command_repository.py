from dairyos.operations.workforce_intelligence.models.workforce_command_snapshot import (
    WorkforceCommandSnapshot,
)



class WorkforceCommandRepository:
    """
    Stores workforce command snapshots.
    """



    def __init__(
        self,
    ):

        self.snapshots = []



    def save(
        self,
        snapshot: WorkforceCommandSnapshot,
    ):

        self.snapshots.append(
            snapshot
        )

        return snapshot



    def all(
        self,
    ):

        return (
            self.snapshots
        )



    def latest(
        self,
    ):

        if not self.snapshots:

            return None


        return (
            self.snapshots[-1]
        )
