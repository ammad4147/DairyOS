"""Governed measurement policy for Finance expenses.

The ledger amount remains the accounting authority.  This module governs only
the meaning of optional quantity/unit fields and the operational recognition
metadata needed by COP.  Unknown items deliberately have no default unit.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpenseMeasurementPolicy:
    units: tuple[str, ...] = ()
    quantity_kind: str = "amount_only"
    operational_authority: str = "FINANCE"
    generic_entry_allowed: bool = True


_POLICIES: dict[str, ExpenseMeasurementPolicy] = {
    "Semen Straws (Sexed / Conventional)": ExpenseMeasurementPolicy(("straw",), "purchase", "BREEDING_SEMEN_INVENTORY", False),
    "AI Consumables (Sheaths, Gloves, Lube)": ExpenseMeasurementPolicy(("piece", "pair", "mL", "L"), "purchase", "BREEDING_OPERATIONS"),
    "Synchronization Hormones (GnRH, PGF2α)": ExpenseMeasurementPolicy(("dose", "mL", "vial"), "purchase", "HEALTH_BREEDING_INVENTORY"),
    "Vaccinations (FMD, HS, LSD, Anthrax)": ExpenseMeasurementPolicy(("dose", "vial"), "purchase", "VACCINATION_INVENTORY"),
    "Dewormers & Parasiticides": ExpenseMeasurementPolicy(("dose", "mL", "tablet", "vial"), "purchase", "HEALTH_INVENTORY"),
    "Mastitis Injectables & Intramammary Tubes": ExpenseMeasurementPolicy(("dose", "mL", "tube", "vial"), "purchase", "HEALTH_INVENTORY"),
    "Antibiotics & General Medications": ExpenseMeasurementPolicy(("dose", "mL", "tablet", "tube", "vial"), "purchase", "HEALTH_INVENTORY"),
    "Calving & OB Supplies": ExpenseMeasurementPolicy(("piece", "kit", "pack", "box"), "purchase", "HEALTH_INVENTORY"),
    "Routine Vet Fees / Consultation": ExpenseMeasurementPolicy(("visit", "consultation", "service"), "service"),
    "Lab Testing & Diagnostics": ExpenseMeasurementPolicy(("test", "service"), "service"),
    "Hoof Trimming & Lameness Treatment": ExpenseMeasurementPolicy(("animal", "service"), "service"),
    "Pregnancy Diagnosis / Ultrasound": ExpenseMeasurementPolicy(("examination", "scan", "service"), "service"),
    "AI Inseminator Service Charges": ExpenseMeasurementPolicy(("AI", "service"), "service"),
    "Daily / Temporary Labor": ExpenseMeasurementPolicy(("worker-hour", "worker-day", "job"), "work_period"),
    "Electricity / Power": ExpenseMeasurementPolicy(("kWh", "billing period"), "period"),
    "Generator Fuel (Diesel / Petrol)": ExpenseMeasurementPolicy(("L",), "period_or_expense"),
    "LPG / Gas": ExpenseMeasurementPolicy(("L", "kg", "cylinder"), "period_or_expense"),
    "Insurance Premiums": ExpenseMeasurementPolicy(("policy period",), "period"),
    "Farm Land Lease / Rent": ExpenseMeasurementPolicy(("coverage period",), "period"),
    "Permits / Licenses / Compliance Fees": ExpenseMeasurementPolicy(("validity period",), "period"),
    "Security / Watchman Services": ExpenseMeasurementPolicy(("service period",), "period"),
    "Acid Cleaner (Milkstone Remover)": ExpenseMeasurementPolicy(("L", "kg"), "period_or_expense"),
    "Alkaline CIP Detergent": ExpenseMeasurementPolicy(("L", "kg"), "period_or_expense"),
    "Chlorine / Sanitizer": ExpenseMeasurementPolicy(("mL", "L", "kg"), "period_or_expense"),
    "Teat Dip (Pre & Post Dip)": ExpenseMeasurementPolicy(("mL", "L"), "period_or_expense"),
    "Udder Towels / Wipes": ExpenseMeasurementPolicy(("piece", "roll", "pack"), "period_or_expense"),
    "Milk Filters / Strainers": ExpenseMeasurementPolicy(("piece", "pack"), "period_or_expense"),
    "PPE / Gloves / Aprons": ExpenseMeasurementPolicy(("piece", "pair", "box"), "period_or_expense"),
    "Animal Bedding (Sand, Sawdust, Straw)": ExpenseMeasurementPolicy(("kg", "tonne", "bale", "bag", "m³"), "period_or_expense"),
    "Milk Transport & Delivery Fuel": ExpenseMeasurementPolicy(("L",), "period_or_expense"),
}


def measurement_policy(item: str | None) -> ExpenseMeasurementPolicy:
    return _POLICIES.get(str(item or "").strip(), ExpenseMeasurementPolicy())


def allowed_units(item: str | None) -> tuple[str, ...]:
    return measurement_policy(item).units


def validate_unit(item: str | None, unit: str | None) -> None:
    """Reject an explicit unit that is not meaningful for the selected item."""
    if not unit:
        return
    policy = measurement_policy(item)
    if policy.units and unit not in policy.units:
        raise ValueError(
            f"Unit {unit!r} is not valid for {item!r}; choose one of: {', '.join(policy.units)}."
        )


def policy_catalog(items: list[str]) -> dict[str, dict[str, object]]:
    return {
        item: {
            "units": list(allowed_units(item)),
            "quantity_kind": measurement_policy(item).quantity_kind,
            "operational_authority": measurement_policy(item).operational_authority,
            "generic_entry_allowed": measurement_policy(item).generic_entry_allowed,
        }
        for item in items
    }
