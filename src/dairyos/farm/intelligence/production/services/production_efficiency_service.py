from dairyos.farm.intelligence.production.models.production_efficiency import (
    ProductionEfficiency,
)



class ProductionEfficiencyService:
    """
    Calculates dairy production efficiency with currency context.
    """

    def __init__(
        self,
        currency: str = "PKR",
        feed_cost_threshold_per_litre: float = 120.0,
    ):
        self.currency = currency
        self.feed_cost_threshold_per_litre = feed_cost_threshold_per_litre

    def evaluate(
        self,
        milk_litres: float,
        milking_animals: int,
        feed_cost: float,
        threshold_override: float | None = None,
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

        threshold = (
            threshold_override
            if threshold_override is not None
            else self.feed_cost_threshold_per_litre
        )

        if feed_cost_per_litre > threshold:
            status = "attention"
        else:
            status = "normal"

        res = ProductionEfficiency(
            milk_litres=milk_litres,
            milking_animals=milking_animals,
            feed_cost=feed_cost,
            feed_cost_per_litre=feed_cost_per_litre,
            litres_per_animal=litres_per_animal,
            efficiency_status=status,
        )
        setattr(res, "currency", self.currency)
        return res
