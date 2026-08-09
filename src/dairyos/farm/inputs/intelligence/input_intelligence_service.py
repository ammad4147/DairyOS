from dairyos.farm.inputs.intelligence.input_intelligence import (
    OperationalInputIntelligence,
)



class InputIntelligenceService:
    """
    Converts analytical metrics into operational intelligence.
    """


    def __init__(
        self,
        analysis_service,
    ):

        self.analysis_service = (
            analysis_service
        )



    def evaluate(
        self,
    ):

        metrics = (
            self.analysis_service
            .generate_metrics()
        )


        signals = []

        recommendations = []

        risk_level = "NORMAL"


        for result in metrics.analysis_results:

            if result.signals:

                signals.extend(
                    result.signals
                )


            if result.status == "ATTENTION":

                risk_level = "HIGH"


            elif (
                result.status == "WATCH"
                and
                risk_level == "NORMAL"
            ):

                risk_level = "MEDIUM"



            for signal in result.signals:

                recommendations.append(
                    f"Review {signal}"
                )



        return OperationalInputIntelligence(

            completeness_score=
                metrics.completeness_score,


            missing_inputs=
                metrics.required_input_gaps,


            attention_required=
                (
                    len(metrics.required_input_gaps) > 0
                    or
                    len(signals) > 0
                ),


            signals=signals,


            risk_level=risk_level,


            recommendations=recommendations,

        )



    def summary(
        self,
    ):

        return self.evaluate()
