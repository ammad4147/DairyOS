from typing import List

from ..models.review_cycle import ReviewCycle


class ReviewManagementService:
    """
    Manages operational review cycles.
    """

    def __init__(self):
        self.cycles: List[ReviewCycle] = []


    def register_cycle(
        self,
        cycle: ReviewCycle,
    ) -> ReviewCycle:

        self.cycles.append(cycle)

        return cycle


    def get_cycles(self) -> List[ReviewCycle]:

        return list(self.cycles)
