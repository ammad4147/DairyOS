"""Governed OPEX classification and COP attribution policy."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

COP_CLASSIFICATIONS = frozenset({"OPEX", "NON_OPEX"})
ATTRIBUTION_METHODS = frozenset({"DIRECT", "PERIODIC", "CONSUMPTION", "ALLOCATED"})

NON_OPEX_ITEMS = frozenset({
    "Equipment Purchase",
    "Loan Interest",
})

CONDITIONAL_ITEMS = frozenset({
    "Other",
    "Small Tools & Implements",
    "Building / Yard Repairs",
    "Taxes / Local Fees",
})

CONDITIONAL_METHOD_ITEMS = frozenset({
    "Tractor Diesel & Servicing",
    "Farm Vehicle Fuel & Maintenance",
    "Water Pumping & Borehole Maintenance",
})

PERIODIC_ITEMS = frozenset({
    "Milker Wages",
    "Feeder / Shed Worker Wages",
    "Supervisor / Farm Manager Salary",
    "Overtime / Bonus Payments",
    "Staff Rations & Living Expenses",
    "Payroll Taxes / Benefits",
    "Grid Electricity (WAPDA)",
    "Internet / Mobile Communications",
    "Accounting & Banking Fees",
    "Bank Charges",
    "Insurance Premiums",
    "Permits / Licenses / Compliance Fees",
    "Security / Watchman Services",
    "Taxes / Local Fees",
    "Farm Land Lease / Rent",
})

DIRECT_ITEMS = frozenset({
    "Routine Vet Fees / Consultation",
    "Vaccinations (FMD, HS, LSD, Anthrax)",
    "Lab Testing & Diagnostics",
    "Hoof Trimming & Lameness Treatment",
    "Pregnancy Diagnosis / Ultrasound",
    "AI Inseminator Service Charges",
    "Daily / Temporary Labor",
    "Generator Service & Spare Parts",
    "Solar System Maintenance & Inverter Servicing",
    "Water Pumping & Borehole Maintenance",
    "Milk Chiller / Cooling Tank Maintenance",
    "Silage Cutter / Feed Mixer Repairs",
    "Shed Maintenance & Plumbing Repairs",
    "Fencing / Gate Repairs",
    "Manure Handling / Removal",
    "Drainage / Wastewater Handling",
    "Pest Control",
    "Deadstock / Biosecurity Disposal",
    "Mortality Disposal / Burial",
    "Custom Hire / Contract Services",
    "Land Preparation / Yard Maintenance",
    "Building / Yard Repairs",
})

CONSUMPTION_ITEMS = frozenset({
    "Semen Straws (Sexed / Conventional)",
})

ALLOCATED_ITEMS = frozenset({
    "Dewormers & Parasiticides",
    "Mastitis Injectables & Intramammary Tubes",
    "Antibiotics & General Medications",
    "Calving & OB Supplies",
    "AI Consumables (Sheaths, Gloves, Lube)",
    "Synchronization Hormones (GnRH, PGF2α)",
    "Generator Fuel (Diesel / Petrol)",
    "LPG / Gas",
    "Milking Machine Liners, Tubes & Oil",
    "Tractor Diesel & Servicing",
    "Farm Vehicle Fuel & Maintenance",
    "Small Tools & Implements",
    "Acid Cleaner (Milkstone Remover)",
    "Alkaline CIP Detergent",
    "Chlorine / Sanitizer",
    "Teat Dip (Pre & Post Dip)",
    "Udder Towels / Wipes",
    "Milk Filters / Strainers",
    "Shed Disinfectants & Lime Powder",
    "PPE / Gloves / Aprons",
    "Animal Bedding (Sand, Sawdust, Straw)",
    "Milk Transport & Delivery Fuel",
    "Packaging / Milk Cans",
    "Office / Stationery / Printing",
})

def default_cop_classification(master_category: str | None, sub_category: str | None) -> str | None:
    master = str(master_category or "").strip().upper()
    item = str(sub_category or "").strip()
    if master != "OPEX":
        return None
    if item in CONDITIONAL_ITEMS:
        return None
    return "NON_OPEX" if item in NON_OPEX_ITEMS else "OPEX"

def default_attribution_method(sub_category: str | None) -> str | None:
    item = str(sub_category or "").strip()
    if item in NON_OPEX_ITEMS or item in CONDITIONAL_METHOD_ITEMS:
        return None
    if item in DIRECT_ITEMS:
        return "DIRECT"
    if item in PERIODIC_ITEMS:
        return "PERIODIC"
    if item in CONSUMPTION_ITEMS:
        return "CONSUMPTION"
    if item in ALLOCATED_ITEMS:
        return "ALLOCATED"
    return None

def attributed_amount(row, period_start: date, period_end: date) -> tuple[Decimal, str]:
    """Return amount attributable to the requested inclusive date range and status."""
    classification = str(getattr(row, "cop_classification", "") or "").upper()
    if classification == "NON_OPEX":
        return Decimal("0.00"), "NON_OPEX"
    if classification != "OPEX":
        return Decimal("0.00"), "UNATTRIBUTED"

    method = str(getattr(row, "cop_attribution_method", "") or "").upper()
    amount = Decimal(str(getattr(row, "amount", 0) or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if method == "DIRECT":
        service_date = getattr(row, "cop_service_date", None)
        if service_date is None:
            return Decimal("0.00"), "UNATTRIBUTED"
        return (amount, "ATTRIBUTED") if period_start <= service_date <= period_end else (Decimal("0.00"), "OUTSIDE_PERIOD")

    if method in {"PERIODIC", "ALLOCATED"}:
        start = getattr(row, "cop_coverage_start", None)
        end = getattr(row, "cop_coverage_end", None)
        if start is None or end is None or end < start:
            return Decimal("0.00"), "UNATTRIBUTED"
        overlap_start = max(period_start, start)
        overlap_end = min(period_end, end)
        if overlap_end < overlap_start:
            return Decimal("0.00"), "OUTSIDE_PERIOD"
        covered_days = (end - start).days + 1
        overlap_days = (overlap_end - overlap_start).days + 1
        return (amount * Decimal(overlap_days) / Decimal(covered_days)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "ATTRIBUTED"

    # Consumption is eligible only when an authoritative usage linkage exists.
    # Until such a linkage is resolved by a domain service, it remains unattributed.
    return Decimal("0.00"), "UNATTRIBUTED"
