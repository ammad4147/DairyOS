"""Authoritative reference/master-data endpoint for operator dropdowns."""
from __future__ import annotations

from fastapi import APIRouter

from dairyos.data.repositories.repository_factory import RepositoryFactory

router = APIRouter(prefix="/farm/reference-data", tags=["reference-data"])

# These are controlled domain vocabularies, not placeholder UI options.  They
# remain explicit until a dedicated master-data table is introduced; every
# response identifies whether a list is persisted or governed vocabulary.
GOVERNED = {
    "animal_types": ["CATTLE"],
    "sexes": ["FEMALE", "MALE"],
    "lifecycle_statuses": ["CALF", "HEIFER", "LACTATING", "DRY", "SOLD", "DECEASED"],
    "milking_frequencies": ["TWICE_DAILY", "THRICE_DAILY"],
    "milking_sessions": ["MORNING", "AFTERNOON", "EVENING"],
    "milking_session_statuses": ["RECORDED", "NOT_MILKED"],
    "milking_session_skip_reasons": [
        "EQUIPMENT_FAILURE", "POWER_OUTAGE", "LABOUR_UNAVAILABLE", "WEATHER",
        "HERD_MOVEMENT", "VETERINARY_HOLD", "OTHER",
    ],
    "feed_types": [
        "SILAGE", "VANDA", "WHEAT_STRAW", "SOYBEAN_MEAL", "MOLASSES",
        "MINERAL_MIXTURE", "BYPASS_FAT", "ANIONIC_SALTS", "TOXIN_BINDER", "AMINO_ACIDS",
    ],
    "health_severities": ["NORMAL", "LOW", "MODERATE", "SEVERE", "CRITICAL"],
    "breeding_event_types": [
        "HEAT_OBSERVED", "AI", "PREGNANCY_CONFIRMED", "PREGNANCY_NEGATIVE", "DRY_OFF", "CALVING",
    ],
    "financial_transaction_types": ["INCOME", "EXPENSE"],
    "financial_categories": [
        "MILK_SALES", "FEED", "HEALTH", "BREEDING", "LABOUR", "UTILITIES", "EQUIPMENT", "OTHER_OPERATING",
    ],
    "payment_types": ["CASH", "BANK", "TRANSFER", "CARD", "OTHER"],
    "workforce_roles": ["VETERINARIAN", "HERDSMAN", "MILKER", "FEEDER", "MANAGER", "ADMIN"],
    "equipment_states": ["AVAILABLE", "IN_USE", "MAINTENANCE", "OUT_OF_SERVICE"],
}


@router.get("")
def reference_data():
    factory = RepositoryFactory.create()
    try:
        animals = factory.animal().get_all()
        drugs = factory.drug_reference().get_all()
        breeds = sorted({a.breed for a in animals if getattr(a, "breed", None)})
        animal_choices = [
            {
                "animal_id": a.animal_id,
                "label": a.animal_id,
                "breed": a.breed,
                "lifecycle_status": a.lifecycle_status,
            }
            for a in animals
            if a.active
        ]
        drug_choices = [
            {
                "drug_id": getattr(d, "id", None),
                "name": getattr(d, "drug_name", None) or getattr(d, "name", None),
                "withdrawal_days": getattr(d, "withdrawal_days", None),
            }
            for d in drugs
        ]
        return {
            "source_policy": {
                "persisted": "animal_choices, breeds, drug_choices",
                "governed_vocabulary": "controlled domain enums in this endpoint",
                "placeholder_values_allowed": False,
            },
            "persisted": {
                "animals": animal_choices,
                "breeds": breeds,
                "drugs": drug_choices,
            },
            "governed": GOVERNED,
        }
    finally:
        factory.close()
