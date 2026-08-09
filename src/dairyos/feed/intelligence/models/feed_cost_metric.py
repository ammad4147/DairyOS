from dataclasses import dataclass


@dataclass
class FeedCostMetric:

    animal_group: str
    feed_cost: float
    milk_revenue: float


    @property
    def feed_cost_ratio(self) -> float:

        if self.milk_revenue == 0:
            return 0

        return (
            self.feed_cost
            /
            self.milk_revenue
        )
