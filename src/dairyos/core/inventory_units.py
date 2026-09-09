"""Explicit inventory conversions; unknown units are never guessed."""
import math
from decimal import Decimal


class InventoryIntegrityError(ValueError):
    pass


MASS_KG = {"kg": Decimal(1), "g": Decimal("0.001"), "tonne": Decimal(1000), "tonnes": Decimal(1000)}


def convert_quantity(value, source: str | None, target: str | None) -> Decimal:
    if not math.isfinite(float(value)):
        raise InventoryIntegrityError("Inventory contains a non-finite quantity; review the original movements.")
    quantity = Decimal(str(value))
    if source == target:
        return quantity
    if source in MASS_KG and target in MASS_KG:
        converted = quantity * MASS_KG[source] / MASS_KG[target]
        if not math.isfinite(float(converted)):
            raise InventoryIntegrityError("Converted inventory quantity exceeds the supported range.")
        return converted
    raise InventoryIntegrityError(
        f"Inventory units {source!r} and {target!r} cannot be combined without an explicit conversion."
    )
