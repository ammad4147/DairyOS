from ..models.milk_sale import MilkSale



class MilkSalesManagementService:



    def evaluate(

        self,

        sale_id,

        milk_quantity_litres,

        selling_price_per_litre

    ):


        daily_revenue = (

            milk_quantity_litres *

            selling_price_per_litre

        )



        if daily_revenue > 0:

            status = "ACTIVE"

            action = "Continue milk sales operations"


        else:

            status = "NO SALES"

            action = "Review production or sales issue"



        return MilkSale(

            sale_id,

            milk_quantity_litres,

            selling_price_per_litre,

            daily_revenue,

            status,

            action

        )
