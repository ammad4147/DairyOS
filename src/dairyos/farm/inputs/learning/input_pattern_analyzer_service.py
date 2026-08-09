from collections import Counter


from dairyos.farm.inputs.learning.input_pattern import (
    OperationalInputPattern,
)


class InputPatternAnalyzerService:
    """
    Learns operational input patterns
    from historical records.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def analyze(
        self,
    ):

        records = (
            self.repository
            .list_all()
        )


        counts = Counter(

            record.input_type

            for record in records

        )


        patterns = []


        for input_type, frequency in counts.items():

            patterns.append(

                OperationalInputPattern(

                    input_type=input_type,

                    expected_frequency=frequency,

                    observed_frequency=frequency,

                    reliability_score=1.0,

                )

            )


        return patterns
