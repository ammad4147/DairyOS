from ..models.financial_forecast import FinancialForecast



class FinancialForecastService:



    def forecast(

        self,

        period,

        milk_output,

        milk_price,

        expenses

    ):


        revenue = milk_output * milk_price


        profit = revenue - expenses



        if profit > 0:

            status = "POSITIVE"



        elif profit == 0:

            status = "BREAK_EVEN"



        else:

            status = "NEGATIVE"



        return FinancialForecast(

            period,

            milk_output,

            milk_price,

            revenue,

            expenses,

            profit,

            status

        )
