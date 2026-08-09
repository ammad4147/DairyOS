from dataclasses import dataclass, field


@dataclass
class OperationalInputIntelligence:
    """
    Intelligence signal generated from operational inputs.
    """

    completeness_score: float

    missing_inputs: list

    attention_required: bool

    signals: list = field(
        default_factory=list
    )

    risk_level: str = "NORMAL"

    recommendations: list = field(
        default_factory=list
    )
