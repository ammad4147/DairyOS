from ..models.cash_flow_summary import CashFlowSummary



class CashFlowService:



    def evaluate(

        self,

        opening_cash,

        income,

        expenses

    ):


        net_cash_movement = income - expenses

        closing_cash = opening_cash + net_cash_movement



        if closing_cash >= 0:

            status = "POSITIVE"

            action = "Maintain current operations"



        else:

            status = "NEGATIVE"

            action = "Immediate cash recovery required"



        return CashFlowSummary(

            opening_cash,

            income,

            expenses,

            net_cash_movement,

            closing_cash,

            status,

            action

        )
