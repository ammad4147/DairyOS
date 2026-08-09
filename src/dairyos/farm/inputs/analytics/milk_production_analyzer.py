from dairyos.farm.inputs.analytics.input_analysis_result import (
    OperationalInputAnalysisResult,
)


class MilkProductionAnalyzer:
    """
    Generates intelligence signals
    from milk production inputs.
    """


    def analyze(
        self,
        records,
    ):

        results = []


        for record in records:

            payload = record.payload


            yield_value = payload.get(
                "total_yield"
            )


            if yield_value is None:
                continue


            status = "NORMAL"

            signals = []


            if yield_value < 20:

                status = "ATTENTION"

                signals.append(
                    "LOW_YIELD"
                )


            elif yield_value < 25:

                status = "WATCH"

                signals.append(
                    "BELOW_TARGET"
                )


            results.append(

                OperationalInputAnalysisResult(

                    input_type=
                        "milk_production",

                    metric=
                        "daily_yield",

                    value=
                        yield_value,

                    status=
                        status,

                    signals=
                        signals,

                    metadata={
                        "animal_id":
                            payload.get(
                                "animal_id"
                            )
                    },
                )

            )


        return results
