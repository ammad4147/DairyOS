from dairyos.farm.operations.services.daily_milk_production_command_view import (
    DailyMilkProductionCommandView,
)


class DailyMilkProductionCommandViewService:
    """Builds the daily milk production command view.

    This read-side projection never accepts a caller-supplied previous total.
    Date comparison belongs to the dated milk trend intelligence service and
    individual/ herd drop detection boundaries.
    """

    def __init__(
        self,
        milk_production_intelligence_service,
        milk_production_trend_intelligence_service=None,
    ):
        self.milk_production_intelligence_service = (
            milk_production_intelligence_service
        )
        self.milk_production_trend_intelligence_service = (
            milk_production_trend_intelligence_service
        )

    def generate(self):
        intelligence = self.milk_production_intelligence_service.generate()
        trend = {}

        if self.milk_production_trend_intelligence_service is not None:
            trend = (
                self.milk_production_trend_intelligence_service
                .generate()
                .summary()
            )

        exceptions = list(intelligence.missing_checkpoints)
        signals = list(intelligence.operational_signals)

        return DailyMilkProductionCommandView(
            total_litres=intelligence.total_litres,
            production_status=intelligence.production_status,
            session_compliance={
                "expected": len(intelligence.expected_checkpoints),
                "completed": len(intelligence.completed_checkpoints),
                "missing": len(intelligence.missing_checkpoints),
            },
            production_trend=trend,
            yield_variance={
                "daily_total_litres": intelligence.total_litres,
            },
            group_yield={
                "shift_production": intelligence.shift_production,
                "shift_contribution": intelligence.shift_contribution,
            },
            exceptions=exceptions,
            signals=signals,
        )

    def summary(self):
        return self.generate().summary()
