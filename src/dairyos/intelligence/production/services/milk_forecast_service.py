from ..models.milk_forecast import MilkForecast



class MilkForecastService:



    def forecast(

        self,

        group_id,

        current_output,

        historical_average

    ):


        forecast_output = (

            current_output +

            historical_average

        ) / 2



        if forecast_output > historical_average:

            trend = "INCREASING"

            status = "POSITIVE"



        elif forecast_output < historical_average:

            trend = "DECREASING"

            status = "ATTENTION"



        else:

            trend = "STABLE"

            status = "NORMAL"



        return MilkForecast(

            group_id,

            current_output,

            historical_average,

            forecast_output,

            trend,

            status

        )
