from dairyos.farm.intelligence.production.models.production_efficiency import (
    ProductionEfficiency,
)



class ProductionEfficiencyService:
    """
    Calculates dairy production efficiency.
    """



    def evaluate(
        self,
        milk_litres: float,
        milking_animals: int,
        feed_cost: float,
    ):


        litres_per_animal = (

            milk_litres / milking_animals

            if milking_animals

            else 0

        )


        feed_cost_per_litre = (

            feed_cost / milk_litres

            if milk_litres

            else 0

        )


        if feed_cost_per_litre > 120:

            status = "attention"

        else:

            status = "normal"



        return ProductionEfficiency(

            milk_litres=milk_litres,

            milking_animals=milking_animals,

            feed_cost=feed_cost,

            feed_cost_per_litre=feed_cost_per_litre,

            litres_per_animal=litres_per_animal,

            efficiency_status=status,
        )
