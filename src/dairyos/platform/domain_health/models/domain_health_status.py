from dataclasses import dataclass



@dataclass
class DomainHealthStatus:

    domain: str

    status: str

    message: str

