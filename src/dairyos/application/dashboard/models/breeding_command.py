from dataclasses import dataclass


@dataclass
class BreedingCommand:
    """
    Dashboard command view for breeding operations.

    Read model only.
    """

    heats_detected: int = 0

    inseminations: int = 0

    pregnancy_confirmations: int = 0

    pending_checks: int = 0

    breeding_alerts: list = None

    def __post_init__(self):
        if self.breeding_alerts is None:
            self.breeding_alerts = []
