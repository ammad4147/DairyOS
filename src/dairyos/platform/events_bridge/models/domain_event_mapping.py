from dataclasses import dataclass



@dataclass
class DomainEventMapping:

    domain: str

    event_name: str

    description: str

