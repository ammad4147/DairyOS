from dataclasses import dataclass
from datetime import UTC, datetime

from dairyos.platform.notification.models.notification_channel import (
    NotificationChannel,
)
from dairyos.platform.notification.models.notification_status import NotificationStatus


@dataclass
class Notification:

    title: str
    message: str
    channel: NotificationChannel

    status: NotificationStatus = NotificationStatus.CREATED

    recipient: str = ""
    source: str = ""

    created_at: datetime = datetime.now(UTC)
