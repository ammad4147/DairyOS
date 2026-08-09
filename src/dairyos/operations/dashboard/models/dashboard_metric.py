from enum import Enum


class DashboardMetric(Enum):
    """
    Operations dashboard indicators.
    """

    OPEN_ISSUES = "OPEN_ISSUES"
    RESOLUTION_RATE = "RESOLUTION_RATE"
    EFFECTIVENESS_SCORE = "EFFECTIVENESS_SCORE"
