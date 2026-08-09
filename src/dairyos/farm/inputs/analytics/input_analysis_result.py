from dataclasses import dataclass, field


@dataclass
class OperationalInputAnalysisResult:
    """
    Standard analytical result produced
    from operational farm inputs.

    Represents intelligence generated
    from operational records.
    """

    input_type: str

    metric: str

    value: float | int | None = None

    status: str = "UNKNOWN"

    signals: list[str] = field(
        default_factory=list
    )

    recommendations: list[str] = field(
        default_factory=list
    )

    metadata: dict = field(
        default_factory=dict
    )
