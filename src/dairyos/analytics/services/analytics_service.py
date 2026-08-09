from ..models.farm_metric import FarmMetric



class AnalyticsService:



    def evaluate(

        self,

        metric_name,

        value,

        unit,

        previous_value

    ):


        if value > previous_value:

            trend = "POSITIVE"


        elif value < previous_value:

            trend = "NEGATIVE"


        else:

            trend = "STABLE"



        if trend == "NEGATIVE":

            performance = "ATTENTION"


        else:

            performance = "GOOD"



        return FarmMetric(

            metric_name,

            value,

            unit,

            trend,

            performance

        )
