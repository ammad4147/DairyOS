from dairyos.operations.workforce_intelligence.models.workforce_ownership_snapshot import (
    WorkforceOwnershipSnapshot,
)


class WorkforceOwnershipRepository:
    """
    Stores workforce ownership snapshots.
    """


    def __init__(
        self,
    ):

        self.snapshots = []



    def save(
        self,
        snapshot: WorkforceOwnershipSnapshot,
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
