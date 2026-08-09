class WorkforceReliabilityRepository:
    """
    Stores workforce reliability snapshots.
    """


    def __init__(
        self,
    ):

        self._snapshots = []



    def save(
        self,
        snapshot,
    ):

        self._snapshots.append(
            snapshot
        )

        return snapshot



    def all(
        self,
    ):

        return list(
            self._snapshots
        )



    def latest(
        self,
    ):

        if not self._snapshots:

            return None


        return self._snapshots[-1]
