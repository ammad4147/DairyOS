from ..models.owner_financial_cockpit import OwnerFinancialCockpit



class OwnerFinancialCockpitService:



    def evaluate(

        self,

        revenue,

        expenses,

        cash_position

    ):


        profit = revenue - expenses



        if profit > 0 and cash_position >= 0:

            financial_status = "HEALTHY"

            owner_action = "Continue operations"



        elif cash_position < 0:

            financial_status = "CASH RISK"

            owner_action = "Immediate intervention required"



        else:

            financial_status = "ATTENTION"

            owner_action = "Review business performance"



        return OwnerFinancialCockpit(

            revenue,

            expenses,

            profit,

            cash_position,

            financial_status,

            owner_action

        )
