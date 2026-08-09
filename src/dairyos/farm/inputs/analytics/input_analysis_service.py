from collections import Counter


from dairyos.farm.inputs.analytics.input_metrics import (
    OperationalInputMetrics,
)


from dairyos.farm.inputs.analytics.milk_production_analyzer import (
    MilkProductionAnalyzer,
)



class InputAnalysisService:
    """
    Converts operational input history
    into analytical signals.
    """


    def __init__(
        self,
        repository,
        registry,
    ):

        self.repository = repository

        self.registry = registry

        self.analyzers = [
            MilkProductionAnalyzer(),
        ]



    def generate_metrics(
        self,
    ):

        records = (
            self.repository
            .list_all()
        )


        type_counts = Counter(

            record.input_type

            for record in records

        )


        required_inputs = [

            item.input_type

            for item in self.registry.list_inputs()

            if item.required

        ]


        observed = set(
            type_counts.keys()
        )


        gaps = [

            item

            for item in required_inputs

            if item not in observed

        ]


        completeness_score = (

            100.0

            if not required_inputs

            else (

                (
                    len(required_inputs)
                    -
                    len(gaps)
                )

                /

                len(required_inputs)

                *

                100.0

            )

        )


        analysis_results = []


        for analyzer in self.analyzers:

            analysis_results.extend(

                analyzer.analyze(
                    records
                )

            )


        return OperationalInputMetrics(

            total_inputs=len(records),

            input_type_counts=dict(
                type_counts
            ),

            required_input_gaps=gaps,

            completeness_score=completeness_score,

            analysis_results=analysis_results,

        )
