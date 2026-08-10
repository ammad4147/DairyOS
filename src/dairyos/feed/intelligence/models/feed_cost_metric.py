from dataclasses import dataclass


@dataclass
class FeedCostMetric:

    animal_group: str
    feed_cost: float
    milk_revenue: float
    feed_quantity_kg: float = 0.0
    milk_litres: float = 0.0

    @property
    def feed_cost_revenue_share(self) -> float:
        if self.milk_revenue == 0:
            return 0.0
        return self.feed_cost / self.milk_revenue

    @property
    def feed_cost_ratio(self) -> float:
        """Alias for backward compatibility with revenue share metric."""
        return self.feed_cost_revenue_share

    @property
    def feed_conversion_ratio(self) -> float:
        """True FCR = Kg Feed Consumed / Litres Milk Produced."""
        if self.milk_litres == 0:
            return 0.0
        return self.feed_quantity_kg / self.milk_litres
