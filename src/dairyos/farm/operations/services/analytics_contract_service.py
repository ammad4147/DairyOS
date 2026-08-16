"""Governed backend analytics contract registry."""

from __future__ import annotations


ANALYSIS_CONTRACTS = {
    "yield": {
        "status": "AVAILABLE",
        "title": "Yield",
        "authoritative_sources": [
            "MilkProductionRepository",
            "AnimalMilkingScheduleHistory",
            "AnimalMilkingScheduleService",
            "MilkDailySemantics",
        ],
        "operational_date_basis": "production_date",
        "population": "active animals with governed milking schedules",
        "completeness_requirements": [
            "expected sessions resolved from animal effective frequency",
            "all expected sessions must have admissible outcomes",
            "missing sessions are not converted to zero",
        ],
        "source_metrics": [
            "complete daily milk litres",
            "effective frequency",
            "expected sessions",
            "recorded/skipped/missing sessions",
        ],
        "endpoint": "/farm/milk/analytics",
    },
    "quality": {
        "status": "DEFERRED",
        "title": "Quality & Composition",
        "authoritative_sources": [
            "Milk quality/composition records",
        ],
        "operational_date_basis": "production_date",
        "population": None,
        "completeness_requirements": [
            "quality/composition domain authority must exist",
        ],
        "source_metrics": [],
        "endpoint": None,
    },
    "herd": {
        "status": "AVAILABLE",
        "title": "Herd Performance",
        "authoritative_sources": [
            "AnimalRepository",
            "Animal lifecycle history",
            "MilkProductionRepository",
        ],
        "operational_date_basis": "explicit analysis date range",
        "population": "active animal population for the selected period",
        "completeness_requirements": [
            "animal population must come from persisted Animal Register",
            "unsupported historical values remain unavailable",
        ],
        "source_metrics": [
            "herd size",
            "milking population",
            "youngstock population",
            "milk production",
        ],
        "endpoint": "/farm/kpis/overview",
    },
    "reproduction": {
        "status": "AVAILABLE",
        "title": "Reproduction",
        "authoritative_sources": [
            "BreedingRepository",
            "ReproductiveEventClassifier",
            "AnimalRepository",
        ],
        "operational_date_basis": "breeding event timestamp",
        "population": "animals with persisted breeding records",
        "completeness_requirements": [
            "event chronology must be explicit",
            "unsupported reproductive intervals remain unavailable",
        ],
        "source_metrics": [
            "inseminations",
            "pregnancy checks",
            "confirmed pregnancies",
            "conception rate",
            "calving interval",
            "days open",
        ],
        "endpoint": "/farm/kpis/overview",
    },
    "health": {
        "status": "AVAILABLE",
        "title": "Health Impact",
        "authoritative_sources": [
            "HealthObservationRepository",
            "TreatmentRepository",
            "AnimalRepository",
            "MilkProductionRepository",
        ],
        "operational_date_basis": "observation/treatment/production dates",
        "population": "active animals and persisted health/treatment records",
        "completeness_requirements": [
            "health observations and treatments must have explicit dates",
            "unsupported causal attribution must not be inferred",
        ],
        "source_metrics": [
            "health observations",
            "treatment rate",
            "milk production",
        ],
        "endpoint": "/farm/kpis/overview",
    },
    "feed": {
        "status": "AVAILABLE",
        "title": "Feed & FCPL",
        "authoritative_sources": [
            "FeedRecordRepository",
            "FinancialRepository",
            "MilkProductionRepository",
        ],
        "operational_date_basis": "feeding_date / transaction_date / production_date",
        "population": "persisted feed, finance and milk records",
        "completeness_requirements": [
            "feed observations must have explicit dates",
            "cost-per-litre requires persisted milk and eligible FEED cost",
            "missing financial domains remain explicit",
        ],
        "source_metrics": [
            "feed consumption",
            "feed kg per litre",
            "feed cost per litre",
            "cost-data completeness",
        ],
        "endpoint": "/farm/kpis/overview",
    },
    "sales": {
        "status": "AVAILABLE",
        "title": "Sales & Revenue",
        "authoritative_sources": [
            "MilkDispositionRepository",
            "FinancialRepository",
        ],
        "operational_date_basis": "production_date / transaction_date",
        "population": "persisted milk dispositions and financial transactions",
        "completeness_requirements": [
            "milk sales must originate from persisted dispositions",
            "receipts must originate from persisted financial records",
            "uncollected receivables remain distinct from recognised receipts",
        ],
        "source_metrics": [
            "sale quantity",
            "amount due",
            "amount received",
            "receivable outstanding",
            "milk revenue",
        ],
        "endpoint": "/farm/milk/dispositions",
    },
    "thi": {
        "status": "AVAILABLE",
        "title": "THI vs Yield",
        "authoritative_sources": [
            "Heat Stress Intelligence",
            "MilkProductionRepository",
        ],
        "operational_date_basis": "environmental observation date + production_date",
        "population": "animals/days with persisted environmental and milk observations",
        "completeness_requirements": [
            "THI observations must exist for the selected period",
            "milk observations must use governed production dates",
            "correlation must not be reported when source coverage is insufficient",
        ],
        "source_metrics": [
            "THI observations",
            "complete daily milk production",
        ],
        "endpoint": "/farm/heat-stress/intelligence",
    },
}


class AnalyticsContractService:
    """Expose the governed backend analytics boundary without new calculations."""

    @staticmethod
    def catalog() -> dict:
        return {
            "contract_version": "1.0",
            "status": "OPERATIONAL",
            "operational_date_basis": (
                "All analytics are explicitly date-ranged and must identify "
                "their operational-date basis."
            ),
            "synthetic_values": False,
            "frontend_calculation_authority": False,
            "analyses": ANALYSIS_CONTRACTS,
        }

    @staticmethod
    def get_analysis(name: str) -> dict:
        key = str(name or "").strip().lower()

        contract = ANALYSIS_CONTRACTS.get(key)

        if contract is None:
            raise KeyError(key)

        return {
            "contract_version": "1.0",
            "analysis": key,
            "contract": contract,
            "synthetic_values": False,
            "frontend_calculation_authority": False,
        }
