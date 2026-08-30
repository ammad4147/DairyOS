from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
)


def test_incomplete_production_still_exposes_known_persisted_litres():
    class Row:
        status = "RECORDED"
        total_yield = 75.0
        production_date = "2026-08-30"

    class Repo:
        def get_by_date(self, production_date):
            return [Row()]

    class DummyTrend:
        def generate(self, *, as_of_date, period_days):
            class Snapshot:
                def summary(self):
                    return {
                        "complete": False,
                        "daily_total": None,
                        "total_litres": None,
                    }

            return Snapshot()

    original = MilkReconciliationService._production_total.__func__

    # Directly exercise the persisted-row path while forcing an incomplete
    # trend snapshot.
    service = MilkReconciliationService()

    from dairyos.farm.production.services import (
        milk_reconciliation_service as module,
    )

    original_trend = module.MilkProductionTrendIntelligenceService
    module.MilkProductionTrendIntelligenceService = DummyTrend

    try:
        result = original(
            service,
            __import__("datetime").date(2026, 8, 30),
            production_repository=Repo(),
        )
    finally:
        module.MilkProductionTrendIntelligenceService = original_trend

    assert result["complete"] is False
    assert result["daily_total"] == 75.0
    assert result["total_litres"] == 75.0
    assert result["saleable_litres"] == 75.0
    assert result["withdrawal_litres"] == 0.0
