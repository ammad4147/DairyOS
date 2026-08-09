from dairyos.farm.inputs.learning.input_deviation import (
    OperationalInputDeviation,
)


class InputDeviationDetectionService:
    """
    Detects operational input rhythm deviations.
    """


    def detect(
        self,
        patterns,
    ):

        deviations = []


        for pattern in patterns:

            deviation = (
                pattern.observed_frequency
                <
                pattern.expected_frequency
            )


            deviations.append(

                OperationalInputDeviation(

                    input_type=
                        pattern.input_type,

                    expected_frequency=
                        pattern.expected_frequency,

                    observed_frequency=
                        pattern.observed_frequency,

                    deviation_detected=
                        deviation,

                    severity=
                        "WARNING"
                        if deviation
                        else
                        "NORMAL",

                )

            )


        return deviations
