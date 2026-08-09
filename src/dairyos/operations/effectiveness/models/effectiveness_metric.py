from enum import Enum


class EffectivenessMetric(Enum):
    """
    Operational performance measurement types.
    """

    RESPONSE_TIME = "RESPONSE_TIME"
    RESOLUTION_QUALITY = "RESOLUTION_QUALITY"
    CLOSURE_RATE = "CLOSURE_RATE"
