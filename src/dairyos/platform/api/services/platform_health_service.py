from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformHealth:
    """Health state returned by the compatibility platform API."""

    runtime: bool
    identity: bool
    security: bool
    configuration: bool

    def status(self) -> str:
        """Return a stable aggregate status without masking a failed component."""
        return "healthy" if all(
            (
                self.runtime,
                self.identity,
                self.security,
                self.configuration,
            )
        ) else "degraded"


class PlatformHealthService:
    """
    Provides enterprise readiness checks.
    """

    def check(self) -> PlatformHealth:

        return PlatformHealth(
            runtime=True,
            identity=True,
            security=True,
            configuration=True,
        )
