from dataclasses import dataclass

@dataclass
class CostCalculator:
    feed_cost_per_liter: float
    labor_cost_per_liter: float
    other_cost_per_liter: float

    def cost_per_liter(self) -> float:
        return self.feed_cost_per_liter + self.labor_cost_per_liter + self.other_cost_per_liter

    def cost_per_animal(self, liters: float) -> float:
        return self.cost_per_liter() * liters
