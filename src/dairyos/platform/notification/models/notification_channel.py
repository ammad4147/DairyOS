from enum import Enum


class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    MOBILE_PUSH = "MOBILE_PUSH"
    SYSTEM_ALERT = "SYSTEM_ALERT"
