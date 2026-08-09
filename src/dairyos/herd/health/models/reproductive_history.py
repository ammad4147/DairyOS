from dataclasses import dataclass


@dataclass
class ReproductiveHistory:

    animal_id: str

    previous_services: int

    previous_conceptions: int

    previous_calvings: int

    reproductive_notes: str

    source: str

    verified: bool
