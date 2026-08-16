"""Reconciled implementation dependency and capability contract."""

from __future__ import annotations


CAPABILITIES = {
    "farm_identity_settings": {
        "title": "Farm Identity / Settings",
        "status": "EXTEND",
        "authoritative_service": "FarmSettingsService",
        "route": "/settings",
        "depends_on": [],
        "next_dependency": "Settings frontend consumes backend-authoritative configuration.",
    },
    "animal_passport": {
        "title": "Animal Passport",
        "status": "EXTEND",
        "authoritative_service": "LifetimeAnimalPassportService",
        "route": "/farm/animals/{animal_id}/passport",
        "depends_on": [
            "AnimalRepository",
            "AnimalMilkingScheduleService",
            "operational_date",
        ],
        "next_dependency": "Passport UI must consume the consolidated date-aware read model.",
    },
    "effective_milking_schedule": {
        "title": "Effective-Dated Milking Schedule",
        "status": "LIVE",
        "authoritative_service": "AnimalMilkingScheduleService",
        "route": "/farm/animals/{animal_id}/milking-frequency/history",
        "depends_on": [
            "AnimalRepository",
            "AnimalMilkingScheduleHistory",
            "operational_date",
        ],
        "next_dependency": "All downstream milk consumers must remain resolver-based.",
    },
    "milk_execution_intelligence": {
        "title": "Milk Execution / Intelligence",
        "status": "LIVE",
        "authoritative_service": "MilkProductionTrendIntelligenceService",
        "route": "/farm/milk/analytics",
        "depends_on": [
            "MilkProductionRepository",
            "AnimalMilkingScheduleService",
            "MilkDailySemantics",
        ],
        "next_dependency": "Dashboard and analytics must consume this read contract.",
    },
    "milk_reconciliation": {
        "title": "Milk Reconciliation",
        "status": "LIVE",
        "authoritative_service": "MilkReconciliationService",
        "route": "/farm/milk/reconciliation",
        "depends_on": [
            "MilkProductionTrendIntelligenceService",
            "MilkDispositionRepository",
        ],
        "next_dependency": "No frontend-owned reconciliation logic.",
    },
    "milk_dispositions": {
        "title": "Milk Disposition / Sales",
        "status": "LIVE",
        "authoritative_service": "MilkDispositionRepository",
        "route": "/farm/milk/dispositions",
        "depends_on": [
            "MilkProductionRepository",
            "FinancialRepository",
        ],
        "next_dependency": "Sales analytics consumes persisted dispositions and receipts.",
    },
    "analytics_contract": {
        "title": "Data Analytics Contract",
        "status": "LIVE",
        "authoritative_service": "AnalyticsContractService",
        "route": "/farm/analytics/catalog",
        "depends_on": [
            "governed domain authorities",
            "operational_date",
        ],
        "next_dependency": "Analysis UI cannot invent unsupported metrics.",
    },
    "cmp": {
        "title": "Cost of Milk Production / Scenarios",
        "status": "EXTEND",
        "authoritative_service": "CMPScenarioService",
        "route": "/farm/cmp/scenarios",
        "depends_on": [
            "CostOfProductionService",
            "MilkProductionRepository",
            "FinancialRepository",
        ],
        "next_dependency": "CMP UI must distinguish actuals from scenario assumptions.",
    },
    "dashboard_read_model": {
        "title": "Main Dashboard Read Model",
        "status": "EXTEND",
        "authoritative_service": "DashboardProjectionService",
        "route": "/dashboard",
        "depends_on": [
            "operational_state",
            "milk",
            "herd",
            "health",
            "finance",
        ],
        "next_dependency": "React presentation consumes backend read models only.",
    },
}


class ReconciledImplementationContractService:
    """Single registry for approved backend capability ownership."""

    VERSION = "1.0"

    @classmethod
    def catalog(cls) -> dict:
        return {
            "contract_version": cls.VERSION,
            "authority_rule": (
                "Authoritative domain data is persisted once; higher layers "
                "consume lower-layer truth and do not redefine it."
            ),
            "frontend_calculation_authority": False,
            "orphan_policy": {
                "LIVE": "Must have a live authoritative route.",
                "EXTEND": "Existing capability is live; remaining work is explicitly identified.",
                "DEFER": "Must include a documented blocking reason.",
                "RETIRE": "Must not have an active production route.",
            },
            "capabilities": CAPABILITIES,
        }

    @classmethod
    def capability(cls, name: str) -> dict:
        key = str(name or "").strip().lower()
        if key not in CAPABILITIES:
            raise KeyError(key)

        return {
            "contract_version": cls.VERSION,
            "capability": key,
            "contract": CAPABILITIES[key],
            "frontend_calculation_authority": False,
        }
