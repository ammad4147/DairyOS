from dairyos.platform.digital_twin.forecasting.models.forecast import (
    Forecast,
)



class ForecastEngine:
    """
    Creates operational forecasts.
    """



    def forecast(

        self,

        metric,

        current_value,

        growth_rate,

        horizon_days,

    ):


        predicted = (

            current_value *

            (1 + growth_rate)

        )


        confidence = 0.8



        return Forecast(

            metric=metric,

            current_value=current_value,

            predicted_value=predicted,

            horizon_days=horizon_days,

            confidence=confidence,

        )

