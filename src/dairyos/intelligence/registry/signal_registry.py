from dairyos.intelligence.signals.detectors.milk_variance_detector import (
    MilkVarianceDetector,
)



class IntelligenceSignalRegistry:
    """
    Registry of intelligence detectors.

    Detectors observe operational context.
    They produce intelligence signals.
    They never modify operational facts.
    """



    def __init__(
        self,
        detectors=None,
    ):

        self.detectors = (
            detectors
            if detectors is not None
            else [
                MilkVarianceDetector()
            ]
        )



    def detect(
        self,
        operational_context,
    ):

        signals = []


        for detector in self.detectors:

            signal = detector.detect(
                operational_context
            )


            if signal is not None:

                signals.append(
                    signal
                )


        return signals
