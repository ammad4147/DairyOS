"""Governed vocabulary for the herd-level milking session ledger."""

from enum import Enum


class MilkingSessionStatus(str, Enum):
    """What the farm reports happened to a whole milking session."""

    RECORDED = "RECORDED"
    NOT_MILKED = "NOT_MILKED"


class MilkingSessionSkipReason(str, Enum):
    """Why a milking session did not happen.

    A skipped session is an operational fact that has to be explainable, so
    ``NOT_MILKED`` carries a governed reason rather than free text. ``OTHER``
    exists so an operator is never forced into a wrong category, and is the
    only value that expects accompanying notes.
    """

    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"
    POWER_OUTAGE = "POWER_OUTAGE"
    LABOUR_UNAVAILABLE = "LABOUR_UNAVAILABLE"
    WEATHER = "WEATHER"
    HERD_MOVEMENT = "HERD_MOVEMENT"
    VETERINARY_HOLD = "VETERINARY_HOLD"
    OTHER = "OTHER"
