from dataclasses import dataclass


@dataclass
class Farm:

    name: str

    location: str

    capacity: int

    status: str = "ACTIVE"
