from dataclasses import dataclass


@dataclass
class GovernanceDecision:
    """
    Result of autonomous decision governance evaluation.
    """

    status: str

    reason: str

    approved: bool
