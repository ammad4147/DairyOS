"""Lifecycle states used by the compatibility platform service registry."""

from enum import Enum


class ServiceLifecycle(str, Enum):
    """Explicit states for a registered platform service."""

    REGISTERED = "registered"
    STARTED = "started"
    STOPPED = "stopped"
