from dataclasses import dataclass


@dataclass
class OperationalInputNotification:
    """
    Notification generated from operational input intelligence.
    """

    notification_type: str

    message: str

    severity: str

    requires_attention: bool
