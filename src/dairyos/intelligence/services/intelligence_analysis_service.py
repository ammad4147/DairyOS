from dairyos.intelligence.models.intelligence_signal import (
    IntelligenceSignal,
)


class IntelligenceAnalysisService:
    """
    Analyses intelligence signals.

    Converts detected conditions into
    operational interpretation.

    Does not modify farm data.
    """


    def analyze(
        self,
        signals: list[IntelligenceSignal],
    ):

        if not signals:

            return {

                "status":
                    "NORMAL",

                "priority":
                    "LOW",

                "summary":
                    "No intelligence conditions detected",

                "signals_count":
                    0,

            }



        critical_count = len(

            [
                signal

                for signal in signals

                if signal.severity
                ==
                "CRITICAL"

            ]

        )


        warning_count = len(

            [
                signal

                for signal in signals

                if signal.severity
                ==
                "WARNING"

            ]

        )



        priority = "LOW"

        status = "NORMAL"



        if warning_count > 0:

            priority = "MEDIUM"

            status = "ATTENTION"



        if critical_count > 0:

            priority = "HIGH"

            status = "CRITICAL"



        return {

            "status":
                status,

            "priority":
                priority,

            "summary":
                self._generate_summary(
                    signals
                ),

            "signals_count":
                len(signals),

            "critical_signals":
                critical_count,

            "warning_signals":
                warning_count,

        }



    def _generate_summary(
        self,
        signals,
    ):

        signal_types = [

            signal.signal_type

            for signal in signals

        ]


        return (

            "Operational conditions detected: "

            +

            ", ".join(
                signal_types
            )

        )
