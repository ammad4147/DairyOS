from dairyos.intelligence.signals.signal_detector import (
    SignalDetector,
)



class SignalRegistry:
    """
    Registry of intelligence signal detectors.

    Provides scalable detector discovery.
    """


    def __init__(
        self,
    ):

        self.detectors = []



    def register(
        self,
        detector: SignalDetector,
    ):

        self.detectors.append(
            detector
        )



    def evaluate(
        self,
        operational_context,
    ):

        signals = []


        for detector in self.detectors:

            result = detector.detect(
                operational_context
            )


            if result is None:

                continue


            if isinstance(
                result,
                list,
            ):

                signals.extend(
                    result
                )

            else:

                signals.append(
                    result
                )


        return signals
