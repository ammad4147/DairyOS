"""Operator-facing reading of a Finance ledger row.

``FinancialTransaction`` plus ``transaction_classifier`` remain the Finance
authority. This module adds no new accounting rule. It gives backend
consumers (Reporting first) one shared, labelled reading of facts the ledger
already holds:

* the *nature* of a row (revenue, expense, capital inflow, cash movement);
* its reporting *category group* and *category* labels;
* its *settlement position* (settled or outstanding).

Revenue category codes were previously labelled only inside
``FinanceTab.tsx``. The labels below mirror that screen exactly so a report
never names a revenue stream differently from the Finance tab. An
unrecognised code is never re-classified: it is reported under its own
humanised label in the "Unclassified" group.
"""

from __future__ import annotations

from typing import Any

from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.finance.expense_taxonomy import (
    FEED_TAXONOMY,
    NON_OPEX_TAXONOMY,
    OPEX_TAXONOMY,
)

NATURE_REVENUE = "REVENUE"
NATURE_EXPENSE = "EXPENSE"
NATURE_CAPITAL_INFLOW = "CAPITAL_INFLOW"
NATURE_CASH_MOVEMENT = "CASH_MOVEMENT"
NATURE_UNKNOWN = "UNKNOWN"

NATURE_LABELS = {
    NATURE_REVENUE: "Revenue",
    NATURE_EXPENSE: "Expense",
    NATURE_CAPITAL_INFLOW: "Capital Inflow",
    NATURE_CASH_MOVEMENT: "Cash Movement",
    NATURE_UNKNOWN: "Unclassified",
}

REVENUE_CATEGORY_LABELS = {
    "MILK_SALES": "Milk Sales",
    "MANURE_SALES": "Organic Manure / Dung",
    "MILKING_ANIMAL_SALE": "Milking Animal Sale",
    "DRY_ANIMAL_SALE": "Dry Animal Sale",
    "HEIFER_SALE": "Heifer Sale",
    "FEMALE_CALF_SALE": "Female Calf Sale",
    "MALE_CALF_SALE": "Male Calf Sale",
    "BULL_SALE": "Bull Sale",
    "OTHER_REVENUE": "Other Revenue",
}

ANIMAL_SALE_CATEGORIES = frozenset(
    {
        "MILKING_ANIMAL_SALE",
        "DRY_ANIMAL_SALE",
        "HEIFER_SALE",
        "FEMALE_CALF_SALE",
        "MALE_CALF_SALE",
        "BULL_SALE",
    }
)

REVENUE_GROUP_ORDER = (
    "Milk Sales",
    "Animal Sales",
    "Organic Manure / Dung",
    "Other Revenue",
    "Unclassified Revenue",
)

CASH_CATEGORY_LABELS = {
    "OWNER_INVESTMENT": "Owner Investment / Add Money",
    "OWNER_WITHDRAWAL": "Owner Draw / Withdraw Money",
    "LOAN_PAYMENT": "Loan Payment",
}

EXPENSE_GROUP_LABELS = {
    # FEED master category
    "GREEN_FODDER_SILAGE": "Feed: Green Fodder & Silage",
    "DRY_ROUGHAGES_HAY": "Feed: Dry Roughages & Hay",
    "COMMERCIAL_FEEDS_GRAINS": "Feed: Commercial Feeds & Grains",
    "PROTEIN_MEALS_CAKES": "Feed: Protein Meals & Cakes",
    "MINERALS_PREMIXES_ADDITIVES": "Feed: Minerals, Premixes & Additives",
    # OPEX master category
    "VETERINARY_HERD_HEALTH": "Veterinary & Herd Health",
    "BREEDING_REPRODUCTION": "Breeding & Reproduction",
    "LABOR_SALARIES": "Labour & Salaries",
    "UTILITIES_ENERGY": "Utilities & Energy",
    "MACHINERY_INFRASTRUCTURE": "Machinery & Infrastructure",
    "DAIRY_CHEMICALS_HYGIENE": "Dairy Chemicals & Hygiene",
    "BEDDING_HOUSING_WASTE": "Bedding, Housing & Waste",
    "LOGISTICS_ADMIN_FINANCE": "Logistics, Admin & Finance",
    "LAND_RENT_CUSTOM_SERVICES": "Land, Rent & Custom Services",
    # NON_OPEX master category
    "LIVESTOCK_CAPITAL": "Livestock Capital (Animal Purchase)",
    "CAPITAL_EQUIPMENT": "Capital Equipment",
}

#: Rows written before the governed taxonomy carry only the legacy category.
LEGACY_EXPENSE_GROUP_LABELS = {
    "FEED": "Feed (legacy category)",
    "HEALTH": "Veterinary & Herd Health",
    "BREEDING": "Breeding & Reproduction",
    "LABOUR": "Labour & Salaries",
    "UTILITIES": "Utilities & Energy",
    "EQUIPMENT": "Machinery & Infrastructure",
    "ANIMAL_PURCHASE": "Livestock Capital (Animal Purchase)",
    "OTHER_OPERATING": "Other Operating",
}

MASTER_LABELS = {"FEED": "Feed", "OPEX": "OPEX", "NON_OPEX": "Non-OPEX"}

_TAXONOMY_BY_MASTER = {
    "FEED": FEED_TAXONOMY,
    "OPEX": OPEX_TAXONOMY,
    "NON_OPEX": NON_OPEX_TAXONOMY,
}

_LEGACY_ITEM_ALIASES = {"Grid Electricity (WAPDA)": "UTILITIES_ENERGY"}


def humanize(code: Any) -> str:
    text = str(code or "").strip().replace("_", " ")
    return text.title() if text else "Unspecified"


def nature(row: Any) -> str:
    kind = classifier.normalize_transaction_type(getattr(row, "transaction_type", None))
    if kind in classifier.INCOME_TYPES:
        return NATURE_REVENUE
    if kind in classifier.EXPENSE_TYPES:
        return NATURE_EXPENSE
    if kind in classifier.CASH_INFLOW_ONLY_TYPES:
        return NATURE_CAPITAL_INFLOW
    if kind in classifier.CASH_MOVEMENT_ONLY_TYPES:
        return NATURE_CASH_MOVEMENT
    return NATURE_UNKNOWN


def is_void(row: Any) -> bool:
    return classifier.normalize_status(getattr(row, "status", None)) == "VOID"


def revenue_category(row: Any) -> tuple[str, str, str]:
    """Return ``(group_label, category_code, category_label)`` for revenue."""
    code = str(getattr(row, "category", "") or "").strip().upper() or "OTHER_REVENUE"
    label = REVENUE_CATEGORY_LABELS.get(code)
    if code == "MILK_SALES":
        return "Milk Sales", code, label
    if code in ANIMAL_SALE_CATEGORIES:
        return "Animal Sales", code, label
    if code == "MANURE_SALES":
        return "Organic Manure / Dung", code, label
    if code == "OTHER_REVENUE":
        return "Other Revenue", code, label
    return "Unclassified Revenue", code, humanize(code)


def expense_category(row: Any) -> tuple[str, str, str, str]:
    """Return ``(master_label, group_code, group_label, item_label)``."""
    master = str(getattr(row, "master_category", "") or "").strip().upper()
    item = str(getattr(row, "sub_category", "") or "").strip()
    custom = str(getattr(row, "custom_specification", "") or "").strip()

    if master in _TAXONOMY_BY_MASTER:
        group_code = _LEGACY_ITEM_ALIASES.get(item) if master == "OPEX" else None
        if group_code is None:
            for code, items in _TAXONOMY_BY_MASTER[master].items():
                if item in items:
                    group_code = code
                    break
        if group_code is None or group_code == "CUSTOM":
            group_code = f"{master}_CUSTOM"
            group_label = f"{MASTER_LABELS[master]}: Other / Custom"
        else:
            group_label = EXPENSE_GROUP_LABELS.get(group_code, humanize(group_code))
        item_label = item or "Unspecified"
        if item == "Other" and custom:
            item_label = f"Other: {custom}"
        return MASTER_LABELS[master], group_code, group_label, item_label

    legacy = str(getattr(row, "category", "") or "").strip().upper() or "OTHER_OPERATING"
    group_label = LEGACY_EXPENSE_GROUP_LABELS.get(legacy, humanize(legacy))
    return "Legacy", f"LEGACY_{legacy}", group_label, item or humanize(legacy)


def category_label(row: Any) -> str:
    kind = nature(row)
    if kind == NATURE_REVENUE:
        return revenue_category(row)[2]
    if kind == NATURE_EXPENSE:
        return expense_category(row)[3]
    code = str(getattr(row, "category", "") or "").strip().upper()
    fallback = classifier.normalize_transaction_type(getattr(row, "transaction_type", None))
    return CASH_CATEGORY_LABELS.get(code) or CASH_CATEGORY_LABELS.get(fallback) or humanize(code or fallback)


def group_label(row: Any) -> str:
    kind = nature(row)
    if kind == NATURE_REVENUE:
        return revenue_category(row)[0]
    if kind == NATURE_EXPENSE:
        return expense_category(row)[2]
    return NATURE_LABELS[kind]


def is_outstanding(row: Any) -> bool:
    """Finance settles a transaction in full. A revenue row is outstanding
    only while RECEIVABLE, an expense row only while PAYABLE. RECORDED rows
    are cash at the time of recording, exactly as the Finance tab treats
    them. VOID rows hold no position at all."""
    status = classifier.normalize_status(getattr(row, "status", None))
    return status in {"RECEIVABLE", "PAYABLE"}


def settlement_label(row: Any) -> str:
    status = classifier.normalize_status(getattr(row, "status", None))
    return {
        "RECORDED": "Settled (cash)",
        "RECEIVED": "Received",
        "PAID": "Paid",
        "RECEIVABLE": "Receivable",
        "PAYABLE": "Payable",
        "VOID": "VOID",
    }.get(status, humanize(status))
