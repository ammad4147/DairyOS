from dataclasses import dataclass, field


@dataclass
class OperationalInputMetrics:
    """
    Analytical summary of operational inputs.
    """

    total_inputs: int

    input_type_counts: dict

    required_input_gaps: list

    completeness_score: float

    analysis_results: list = field(
        default_factory=list
    )
