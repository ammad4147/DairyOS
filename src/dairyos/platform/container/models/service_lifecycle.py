from enum import Enum


class ServiceLifecycle(str, Enum):
    REGISTERED = "registered"
    STARTED = "started"
    STOPPED = "stopped"
