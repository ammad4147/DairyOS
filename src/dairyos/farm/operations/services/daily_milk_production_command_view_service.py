from dairyos.farm.operations.services.daily_milk_production_command_view import (
    DailyMilkProductionCommandView,
)


class DailyMilkProductionCommandViewService:
    """
    Builds daily milk production command view.

    Read-side projection only.

    Does not:
        - create milk records
        - alter operational state
        - infer missing production

    Sources:
        - MilkProductionIntelligenceService
        - MilkProductionTrendIntelligenceService
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


    def generate(
        self,
        previous_total_litres: float = 0.0,
    ):

        intelligence = (
            self.milk_production_intelligence_service
            .generate()
        )


        trend = {}


        if self.milk_production_trend_intelligence_service is not None:

            trend = (
                self.milk_production_trend_intelligence_service
                .generate(
                    previous_total_litres
                )
                .summary()
            )


        exceptions = []


        exceptions.extend(
            intelligence.missing_checkpoints
        )


        signals = list(
            intelligence.operational_signals
        )


        if trend.get(
            "signals"
        ):

            signals.extend(
                trend["signals"]
            )


        return DailyMilkProductionCommandView(

            total_litres=(
                intelligence.total_litres
            ),

            production_status=(
                intelligence.production_status
            ),

            session_compliance={

                "expected":
                    len(
                        intelligence.expected_checkpoints
                    ),

                "completed":
                    len(
                        intelligence.completed_checkpoints
                    ),

                "missing":
                    len(
                        intelligence.missing_checkpoints
                    ),

            },

            production_trend=trend,


            yield_variance={

                "daily_total_litres":
                    intelligence.total_litres,

            },


            group_yield={

                "shift_production":
                    intelligence.shift_production,

                "shift_contribution":
                    intelligence.shift_contribution,

            },


            exceptions=exceptions,


            signals=signals,

        )


    def summary(
        self,
        previous_total_litres: float = 0.0,
    ):

        return (
            self.generate(
                previous_total_litres
            )
            .summary()
        )
