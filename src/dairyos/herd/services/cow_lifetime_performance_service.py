from dataclasses import dataclass
from typing import List


@dataclass
class CowLifetimeSummary:
    animal_id: str
    currency: str = "PKR"
    total_lifetime_milk_litres: float = 0.0
    projected_305_day_yield_litres: float = 0.0
    total_lifetime_revenue: float = 0.0
    total_lifetime_feed_cost: float = 0.0
    total_lifetime_health_cost: float = 0.0
    net_lifetime_profitability: float = 0.0
    lactation_count: int = 1
    status: str = "PROFITABLE"


class CowLifetimePerformanceService:
    """
    Tracks individual cow lifetime performance, 305-day ME lactation yield,
    and cumulative lifetime P&L in PKR currency.
    """

    def __init__(
        self,
        default_currency: str = "PKR",
        milk_price_per_litre: float = 220.0,
    ):
        self.default_currency = default_currency
        self.milk_price_per_litre = milk_price_per_litre

    def calculate_305_day_projection(
        self,
        current_lactation_days: int,
        current_lactation_yield_litres: float,
    ) -> float:
        if current_lactation_days <= 0:
            return 0.0
        avg_daily = current_lactation_yield_litres / current_lactation_days
        if current_lactation_days >= 305:
            return round(current_lactation_yield_litres, 2)
        remaining_days = 305 - current_lactation_days
        projected = current_lactation_yield_litres + (
            avg_daily * remaining_days * 0.85
        )
        return round(projected, 2)

    def evaluate_cow_lifetime(
        self,
        animal_id: str,
        total_milk_litres: float,
        feed_cost: float,
        health_cost: float,
        current_lactation_days: int = 100,
        current_lactation_yield: float = 2500.0,
        milk_price_per_litre: float | None = None,
        currency: str | None = None,
    ) -> CowLifetimeSummary:
        curr = currency or self.default_currency
        price = (
            milk_price_per_litre
            if milk_price_per_litre is not None
            else self.milk_price_per_litre
        )

        revenue = total_milk_litres * price
        total_expenses = feed_cost + health_cost
        net_profit = revenue - total_expenses
        status = "PROFITABLE" if net_profit >= 0 else "LOSS"

        proj_305 = self.calculate_305_day_projection(
            current_lactation_days, current_lactation_yield
        )

        return CowLifetimeSummary(
            animal_id=animal_id,
            currency=curr,
            total_lifetime_milk_litres=total_milk_litres,
            projected_305_day_yield_litres=proj_305,
            total_lifetime_revenue=round(revenue, 2),
            total_lifetime_feed_cost=round(feed_cost, 2),
            total_lifetime_health_cost=round(health_cost, 2),
            net_lifetime_profitability=round(net_profit, 2),
            status=status,
        )
