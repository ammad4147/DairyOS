"""
Legacy compatibility alias.

Canonical DairyOS milk-production persistence authority:

    dairyos.data.models.milk_production.MilkProduction

This module must not declare a second ``milk_production_orm`` table.
"""

from dairyos.data.models.milk_production import MilkProduction

MilkProductionORM = MilkProduction

__all__ = ["MilkProductionORM"]
