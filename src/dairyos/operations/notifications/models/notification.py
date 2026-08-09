from dataclasses import dataclass
from datetime import datetime

from .notification_type import NotificationType


@dataclass
class Notification:
    """
    Represents an operational communication.
    """

    notification_id: str
    recipient: str
    message: str
    notification_type: NotificationType
    created_at: datetime
    sent: bool = False
