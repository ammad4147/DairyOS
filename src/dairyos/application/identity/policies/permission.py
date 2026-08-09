from enum import Enum


class Permission(str, Enum):
    """
    Operational permissions within DairyOS.

    Permissions represent allowed farm activities,
    not authentication privileges.
    """

    VIEW_DASHBOARD = "view_dashboard"

    VIEW_HERD_STATUS = "view_herd_status"
    VIEW_PRODUCTION_STATUS = "view_production_status"

    RECORD_MILK = "record_milk"
    VIEW_MILKING_TASKS = "view_milking_tasks"

    RECORD_FEEDING = "record_feeding"
    VIEW_FEED_TASKS = "view_feed_tasks"

    RECORD_HEALTH_EVENT = "record_health_event"
    VIEW_HEALTH_STATUS = "view_health_status"

    RECORD_BREEDING_EVENT = "record_breeding_event"

    VIEW_FINANCIAL_STATUS = "view_financial_status"

    MANAGE_USERS = "manage_users"

    VIEW_ALERTS = "view_alerts"
    ACKNOWLEDGE_ALERTS = "acknowledge_alerts"
