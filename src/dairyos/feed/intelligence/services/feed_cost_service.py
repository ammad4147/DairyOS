from dairyos.feed.intelligence.models import FeedCostMetric


class FeedCostService:


    def calculate_cost_metric(
        self,
        animal_group: str,
        feed_cost: float,
        milk_revenue: float,
    ) -> FeedCostMetric:


        return FeedCostMetric(
            animal_group=animal_group,
            feed_cost=feed_cost,
            milk_revenue=milk_revenue,
        )
