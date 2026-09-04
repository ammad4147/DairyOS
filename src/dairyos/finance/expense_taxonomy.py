"""Governed Finance expense taxonomy for the Feed/OPEX entry modes.

The taxonomy is intentionally kept in one backend module so the API,
reference-data endpoint, validation and tests all use the same vocabulary.
"""
from __future__ import annotations

FEED_TAXONOMY = {
    "GREEN_FODDER_SILAGE": [
        "Corn / Maize Silage",
        "Alfalfa (Lucerne)",
        "Berseem",
        "Rhodes Grass (Fresh)",
        "Sorghum / Sadabahar",
        "Super Napier / Mott Grass",
        "Rye Grass",
    ],
    "DRY_ROUGHAGES_HAY": [
        "Wheat Straw (Bhoosa)",
        "Rhodes Grass Hay",
        "Alfalfa Hay",
        "Corn Stover",
    ],
    "COMMERCIAL_FEEDS_GRAINS": [
        "Commercial Compound Vanda / Cattle Feed",
        "Flaked Corn / Cracked Maize",
        "Wheat Bran (Choker)",
        "Rice Polish",
        "Barley",
        "Broken Rice",
    ],
    "PROTEIN_MEALS_CAKES": [
        "Canola Meal",
        "Soybean Meal (Hi-Pro)",
        "Mustard Cake (Khal Sarson)",
        "Cottonseed Cake (Khal Banola)",
        "Sunflower Meal",
        "Corn Gluten Meal (30% / 60%)",
    ],
    "MINERALS_PREMIXES_ADDITIVES": [
        "Dairy Mineral Premix",
        "Di-Calcium Phosphate (DCP)",
        "Bypass Fat / Rumen-Protected Fat",
        "Sodium Bicarbonate (Buffer)",
        "Toxin Binder",
        "Live Yeast / Probiotics",
        "Molasses",
        "Urea",
        "Rock Salt / Mineral Licking Blocks",
    ],
    "CUSTOM": ["Other"],
}

OPEX_TAXONOMY = {
    "VETERINARY_HERD_HEALTH": [
        "Routine Vet Fees / Consultation",
        "Vaccinations (FMD, HS, LSD, Anthrax)",
        "Dewormers & Parasiticides",
        "Lab Testing & Diagnostics",
        "Hoof Trimming & Lameness Treatment",
        "Mastitis Injectables & Intramammary Tubes",
        "Antibiotics & General Medications",
        "Calving & OB Supplies",
        "Mortality Disposal / Burial",
    ],
    "BREEDING_REPRODUCTION": [
        "Semen Straws (Sexed / Conventional)",
        "AI Consumables (Sheaths, Gloves, Lube)",
        "Synchronization Hormones (GnRH, PGF2α)",
        "Pregnancy Diagnosis / Ultrasound",
        "AI Inseminator Service Charges",
        "Breeding Record / Registration Fees",
    ],
    "LABOR_SALARIES": [
        "Milker Wages",
        "Feeder / Shed Worker Wages",
        "Supervisor / Farm Manager Salary",
        "Daily / Temporary Labor",
        "Overtime / Bonus Payments",
        "Staff Rations & Living Expenses",
        "Payroll Taxes / Benefits",
    ],
    "UTILITIES_ENERGY": [
        "Grid Electricity (WAPDA)",
        "Generator Fuel (Diesel / Petrol)",
        "Generator Service & Spare Parts",
        "Solar System Maintenance & Inverter Servicing",
        "Water Pumping & Borehole Maintenance",
        "LPG / Gas",
        "Internet / Mobile Communications",
    ],
    "MACHINERY_INFRASTRUCTURE": [
        "Milking Machine Liners, Tubes & Oil",
        "Milk Chiller / Cooling Tank Maintenance",
        "Silage Cutter / Feed Mixer Repairs",
        "Tractor Diesel & Servicing",
        "Farm Vehicle Fuel & Maintenance",
        "Shed Maintenance & Plumbing Repairs",
        "Fencing / Gate Repairs",
        "Equipment Purchase",
        "Small Tools & Implements",
    ],
    "DAIRY_CHEMICALS_HYGIENE": [
        "Acid Cleaner (Milkstone Remover)",
        "Alkaline CIP Detergent",
        "Chlorine / Sanitizer",
        "Teat Dip (Pre & Post Dip)",
        "Udder Towels / Wipes",
        "Milk Filters / Strainers",
        "Shed Disinfectants & Lime Powder",
        "PPE / Gloves / Aprons",
    ],
    "BEDDING_HOUSING_WASTE": [
        "Animal Bedding (Sand, Sawdust, Straw)",
        "Manure Handling / Removal",
        "Drainage / Wastewater Handling",
        "Pest Control",
        "Deadstock / Biosecurity Disposal",
    ],
    "LOGISTICS_ADMIN_FINANCE": [
        "Milk Transport & Delivery Fuel",
        "Packaging / Milk Cans",
        "Accounting & Banking Fees",
        "Insurance Premiums",
        "Permits / Licenses / Compliance Fees",
        "Office / Stationery / Printing",
        "Security / Watchman Services",
        "Taxes / Local Fees",
        "Loan Interest / Bank Charges",
    ],
    "LAND_RENT_CUSTOM_SERVICES": [
        "Farm Land Lease / Rent",
        "Custom Hire / Contract Services",
        "Land Preparation / Yard Maintenance",
        "Building / Yard Repairs",
    ],
    "CUSTOM": ["Other"],
}

EXPENSE_TAXONOMIES = {
    "FEED": FEED_TAXONOMY,
    "OPEX": OPEX_TAXONOMY,
}

MASTER_CATEGORIES = frozenset(EXPENSE_TAXONOMIES)

LEGACY_CATEGORY_BY_MASTER = {
    "FEED": "FEED",
    "OPEX": "OTHER_OPERATING",
}

LEGACY_CATEGORY_BY_OPEX_GROUP = {
    "VETERINARY_HERD_HEALTH": "HEALTH",
    "BREEDING_REPRODUCTION": "BREEDING",
    "LABOR_SALARIES": "LABOUR",
    "UTILITIES_ENERGY": "UTILITIES",
    "MACHINERY_INFRASTRUCTURE": "EQUIPMENT",
    "DAIRY_CHEMICALS_HYGIENE": "OTHER_OPERATING",
    "BEDDING_HOUSING_WASTE": "OTHER_OPERATING",
    "LOGISTICS_ADMIN_FINANCE": "OTHER_OPERATING",
    "LAND_RENT_CUSTOM_SERVICES": "OTHER_OPERATING",
    "CUSTOM": "OTHER_OPERATING",
}


def all_items(master_category: str) -> list[str]:
    """Return every allowed item for a master category, preserving taxonomy order."""
    taxonomy = EXPENSE_TAXONOMIES[master_category]
    return [item for items in taxonomy.values() for item in items]


def valid_item(master_category: str, item: str) -> bool:
    return item in all_items(master_category)


def legacy_category(master_category: str, sub_category: str) -> str:
    """Map the governed new taxonomy onto the legacy category contract."""
    if master_category == "FEED":
        return "FEED"

    for group, items in OPEX_TAXONOMY.items():
        if sub_category in items:
            return LEGACY_CATEGORY_BY_OPEX_GROUP[group]

    return "OTHER_OPERATING"
