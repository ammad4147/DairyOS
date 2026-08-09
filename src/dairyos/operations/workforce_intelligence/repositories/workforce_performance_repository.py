class WorkforcePerformanceRepository:
    """
    Stores workforce performance snapshots.
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



    def latest(
        self,
    ):

        if not self._snapshots:

            return None


        return self._snapshots[-1]



    def all(
        self,
    ):

        return self._snapshots
