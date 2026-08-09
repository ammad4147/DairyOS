from ..models.risk_forecast import RiskForecast



class RiskForecastService:



    def generate(

        self,

        category,

        signal_confidence,

        trend_strength

    ):


        probability = min(

            signal_confidence + trend_strength,

            95

        )


        if probability >= 75:

            risk_level = "HIGH"

        elif probability >= 50:

            risk_level = "MEDIUM"

        else:

            risk_level = "LOW"



        return RiskForecast(

            category,

            f"{category} future risk forecast",

            probability,

            risk_level,

            self._action(category)

        )



    def _action(

        self,

        category

    ):


        actions = {

            "PRODUCTION":

                "Review feed and production factors",

            "HEALTH":

                "Review animal health prevention",

            "REPRODUCTION":

                "Review breeding strategy",

            "FINANCE":

                "Review financial planning"

        }


        return actions.get(

            category,

            "Review farm indicators"

        )



    def requires_action(

        self,

        forecast

    ):


        return forecast.risk_level in (

            "HIGH",

            "MEDIUM"

        )
