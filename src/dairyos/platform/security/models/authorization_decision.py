from dataclasses import dataclass


@dataclass
class AuthorizationDecision:
    """
    Result returned by authorization engine.
    """

    allowed: bool
    reason: str

    @property
    def status(self) -> str:
        return "ALLOW" if self.allowed else "DENY"
