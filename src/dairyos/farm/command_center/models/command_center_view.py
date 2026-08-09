from dataclasses import dataclass, field


@dataclass
class CommandCenterView:
    """
    Owner-facing operational projection.

    Composition model only.
    No business rules.
    """

    status: dict = field(
        default_factory=dict
    )

    attention: list = field(
        default_factory=list
    )

    decisions: dict = field(
        default_factory=dict
    )

    actions: list = field(
        default_factory=list
    )

    confidence: dict = field(
        default_factory=dict
    )
