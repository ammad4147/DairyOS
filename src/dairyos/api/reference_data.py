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
    # Reconciled 2026-08-14 (Phase 1 vocabulary drift fix). SICK deliberately
    # excluded: it is a health condition, not a life stage, and conflating
    # the two meant an animal could not be simultaneously LACTATING and
    # SICK. It will return once HealthCase (G5.1) exists to model it
    # properly as an overlay. This list is the single source of truth —
    # animal_registration.py and animal_management/router.py both validate
    # against it directly rather than keeping their own copies.
    "lifecycle_statuses": [
        "CALF", "HEIFER", "CLOSE_UP", "LACTATING", "DRY",
        "SOLD", "CULLED", "DECEASED",
    ],
    # ONCE_DAILY deliberately excluded: MilkSessionSequenceService has no
    # branch for it (only TWICE_DAILY/THRICE_DAILY are sequenced), and the
    # frontend previously offered it anyway despite no write path ever
    # validating it. Removed from the dropdown to match what's actually
    # supported (2026-08-14) rather than left as a value that silently
    # breaks session sequencing. Flag to the user if once-daily milking is
    # a real need — it would need a third sequencing branch, not just a
    # vocabulary entry.
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
    # Reconciled 2026-08-14 (G6.1 breeding classifier unification) to match
    # what the operator UI's breeding entry form actually sends
    # (src/DairyOS.Web/src/App.tsx's entryConfigs.breeding options) — the
    # previous uppercase list here (HEAT_OBSERVED, AI, PREGNANCY_CONFIRMED,
    # PREGNANCY_NEGATIVE, DRY_OFF, CALVING) was never read by anything and
    # didn't match real submitted data. See
    # dairyos.herd.reproduction.services.reproductive_event_classifier for
    # the single source of truth on how these are classified; that module,
    # not this list, is authoritative — this list documents the real
    # vocabulary for reference/future frontend wiring. abortion,
    # stillbirth and postpartum_observation are accepted by the write path
    # but not yet classified by any of the three reproduction endpoints
    # (pre-existing gap, not addressed by this fix).
    "breeding_event_types": [
        "heat_detected", "insemination", "pregnancy_diagnosis",
        "pregnancy_confirmed", "pregnancy_negative", "dry_off", "calving",
        "abortion", "stillbirth", "postpartum_observation",
    ],
    # Reconciled 2026-08-14 (Phase 1). The operator UI has always offered
    # all six of these (src/DairyOS.Web/src/App.tsx entryConfigs.finance),
    # but this list advertised only INCOME and EXPENSE and every report
    # recognised only those two -- so the other four were persisted, counted,
    # and then contributed nothing to any total. How each is treated in
    # reporting is defined in ONE place:
    # dairyos.finance.classification.transaction_classifier.
    "financial_transaction_types": [
        "INCOME", "EXPENSE", "RECEIPT", "PAYMENT",
        "OWNER_WITHDRAWAL", "LOAN_PAYMENT",
    ],
    "financial_categories": [
        "MILK_SALES", "FEED", "HEALTH", "BREEDING", "LABOUR", "UTILITIES", "EQUIPMENT", "OTHER_OPERATING",
    ],
    # Reconciled 2026-08-14 to match what the operator UI actually offers
    # (CASH/BANK/MOBILE/CREDIT). The previous list advertised TRANSFER, CARD
    # and OTHER -- none of which any form has ever offered -- while omitting
    # MOBILE and CREDIT, which operators do use. As of this release the
    # value is persisted (financial_transactions.payment_method); before it,
    # payment method was accepted by the API and silently discarded.
    "payment_types": ["CASH", "BANK", "MOBILE", "CREDIT"],
    "workforce_roles": ["VETERINARIAN", "HERDSMAN", "MILKER", "FEEDER", "MANAGER", "ADMIN"],
    "equipment_states": ["AVAILABLE", "IN_USE", "MAINTENANCE", "OUT_OF_SERVICE"],
    # Reconciled 2026-08-14 (G8.1, decision confirmed via AskUserQuestion):
    # the operator UI has always offered these six
    # (src/DairyOS.Web/src/App.tsx entryConfigs.inventory), but until now
    # POST /farm/inventory was event-journal-only -- no queryable stock
    # model existed for a vocabulary to even matter to. Direction is fixed
    # per type, not left to the reader to infer:
    # dairyos.data.models.inventory_transaction.InventoryTransaction is the
    # single source of truth for how each type signs `signed_quantity`.
    "inventory_movement_types": [
        "PURCHASE", "RECEIPT", "CONSUMPTION", "TRANSFER", "WASTAGE", "ADJUSTMENT",
    ],
    # Added 2026-08-14 (D3, identity/RBAC rebuild). The five pre-existing
    # "identity" trees each defined their own overlapping role vocabulary
    # (application/identity, core/identity, core/models/role.py,
    # operations/users, platform/identity) but had zero live callers in
    # api/ -- none of it was ever reachable. This is the one role
    # vocabulary the new dairyos.data.models.user.User table and
    # dairyos.api.auth actually enforce. OWNER: full access, including
    # creating/managing other users. MANAGER: day-to-day farm operation.
    # MILKER: operational data entry only. The pre-existing single
    # env-var-configured admin account (DAIRYOS_ADMIN_ROLE) is untouched by
    # this list -- it is a legacy fallback identity, not a governed role,
    # and may still carry an arbitrary string for backward compatibility.
    "auth_roles": ["OWNER", "MANAGER", "MILKER"],
    # Added 2026-08-14 (G5.1, HealthCase). Before HealthCase existed, health
    # observations had a `status` field of their own (default "OPEN") but no
    # status-transition endpoint and no concept of a resolvable case. This is
    # the governed lifecycle of a HealthCase itself: OPEN when opened,
    # RESOLVED only via the explicit POST /farm/health-cases/{case_id}/resolve
    # action -- never inferred from an observation or treatment being
    # recorded.
    "health_case_statuses": ["OPEN", "RESOLVED"],
    # Added 2026-08-14 (AA-013 §4, D-UI-5). The Operational Finding entity:
    # the single lifecycle behind the dashboard action queue, every
    # section's alert list, and nav count badges. `finding_source_modules`
    # must stay a subset of the keys in
    # dairyos.farm.findings.services.operational_finding_service.FINDING_PREFIXES
    # (the single source of truth for the module->prefix mapping, e.g.
    # MILK -> AL, HEALTH -> HL); that module, not this list, is
    # authoritative for prefix allocation.
    "finding_severities": ["CRITICAL", "HIGH", "MONITORING", "INFORMATION"],
    "finding_statuses": ["RAISED", "ACKNOWLEDGED", "RESOLVED"],
    "finding_source_modules": [
        "MILK", "HEALTH", "BREEDING", "INVENTORY", "EQUIPMENT", "FEED", "WORKFORCE", "FINANCE",
    ],
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
