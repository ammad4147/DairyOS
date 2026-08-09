from dataclasses import dataclass



@dataclass
class BootstrapResult:

    started: bool

    services_loaded: int

    runtime_ready: bool
