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



    def evaluate_advanced(

        self,

        sale_id,

        milk_quantity_litres,

        selling_price_per_litre,

        vat_rate_pct: float = 0.0,

        discount_pct: float = 0.0,

        payment_terms: str = "CASH",

        credit_days: int = 0,

    ):

        """

        Advanced sales evaluation with VAT, discount, and credit tracking.

        All new parameters are optional with safe defaults.

        """



        milk_quantity_litres = max(0.0, float(milk_quantity_litres or 0.0))

        selling_price_per_litre = max(0.0, float(selling_price_per_litre or 0.0))

        vat_rate_pct = max(0.0, float(vat_rate_pct or 0.0))

        discount_pct = max(0.0, min(100.0, float(discount_pct or 0.0)))

        credit_days = max(0, int(credit_days or 0))



        subtotal = milk_quantity_litres * selling_price_per_litre

        discount_amount = subtotal * (discount_pct / 100.0)

        taxable_amount = subtotal - discount_amount

        vat_amount = taxable_amount * (vat_rate_pct / 100.0)

        daily_revenue = taxable_amount + vat_amount



        if daily_revenue > 0:

            status = "ACTIVE"

            action = "Continue milk sales operations"

        else:

            status = "NO SALES"

            action = "Review production or sales issue"



        payment_status = "PAID" if payment_terms.upper() == "CASH" else f"DUE_IN_{credit_days}_DAYS"



        return {

            "sale_id": sale_id,

            "milk_quantity_litres": round(milk_quantity_litres, 3),

            "selling_price_per_litre": round(selling_price_per_litre, 4),

            "subtotal": round(subtotal, 2),

            "discount_pct": discount_pct,

            "discount_amount": round(discount_amount, 2),

            "vat_rate_pct": vat_rate_pct,

            "vat_amount": round(vat_amount, 2),

            "daily_revenue": round(daily_revenue, 2),

            "payment_terms": payment_terms.upper(),

            "credit_days": credit_days,

            "payment_status": payment_status,

            "status": status,

            "action": action,

        }
