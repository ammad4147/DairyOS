from dataclasses import dataclass


@dataclass
class Location:

    name: str

    category: str

    active: bool = True
