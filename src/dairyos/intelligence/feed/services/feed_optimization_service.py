from ..models.feed_efficiency import FeedEfficiency



class FeedOptimizationService:



    def evaluate(

        self,

        group_id,

        feed_quantity,

        milk_output

    ):


        if feed_quantity <= 0:

            efficiency = 0

        else:

            efficiency = milk_output / feed_quantity



        if efficiency >= 1.2:

            status = "GOOD"

            recommendation = "Maintain current ration"



        elif efficiency >= 0.8:

            status = "ATTENTION"

            recommendation = "Review ration efficiency"



        else:

            status = "POOR"

            recommendation = "Optimize feeding strategy"



        return FeedEfficiency(

            group_id,

            feed_quantity,

            milk_output,

            efficiency,

            status,

            recommendation

        )
