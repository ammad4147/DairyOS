from dataclasses import dataclass
from enum import Enum


class RuntimeStatus(str, Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class RuntimeState:
    status: RuntimeStatus = RuntimeStatus.CREATED

    active_services: int = 0

    def start(self, service_count: int):
        self.status = RuntimeStatus.RUNNING
        self.active_services = service_count

    def stop(self):
        self.status = RuntimeStatus.STOPPED
        self.active_services = 0
