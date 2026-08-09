from dataclasses import dataclass


@dataclass
class OperationalStatus:

    platform: str

    runtime: str

    healthy: bool

    ready: bool

    domains: dict

    observability: dict
