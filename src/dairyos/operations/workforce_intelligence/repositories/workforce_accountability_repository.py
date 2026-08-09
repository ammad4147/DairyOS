from dairyos.operations.workforce_intelligence.models.workforce_accountability_snapshot import (
    WorkforceAccountabilitySnapshot,
)


class WorkforceAccountabilityRepository:
    """
    Stores workforce accountability snapshots.
    """


    def __init__(
        self,
    ):

        self.snapshots = []



    def save(
        self,
        snapshot: WorkforceAccountabilitySnapshot,
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
