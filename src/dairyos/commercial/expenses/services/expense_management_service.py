from ..models.farm_expense import FarmExpense



class ExpenseManagementService:



    def evaluate(

        self,

        expense_id,

        category,

        amount,

        expense_type

    ):


        if amount > 0:

            status = "ACTIVE"

            action = "Record operating expense"


        else:

            status = "INVALID"

            action = "Review expense entry"



        return FarmExpense(

            expense_id,

            category,

            amount,

            expense_type,

            status,

            action

        )
