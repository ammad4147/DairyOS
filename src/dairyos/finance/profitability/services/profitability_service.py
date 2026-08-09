from ..models.profitability_summary import ProfitabilitySummary



class ProfitabilityService:



    def evaluate(

        self,

        revenue,

        expenses

    ):


        operating_profit = revenue - expenses



        if revenue > 0:

            profit_margin = (

                operating_profit /

                revenue

            ) * 100

        else:

            profit_margin = 0



        if operating_profit > 0:

            status = "PROFITABLE"

            action = "Continue current strategy"



        elif operating_profit == 0:

            status = "BREAK EVEN"

            action = "Monitor performance"



        else:

            status = "LOSS"

            action = "Immediate corrective action required"



        return ProfitabilitySummary(

            revenue,

            expenses,

            operating_profit,

            profit_margin,

            status,

            action

        )
