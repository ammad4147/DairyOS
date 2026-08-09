from dataclasses import dataclass



@dataclass
class OperationalHealthView:

    domain: str

    status: str

    last_update: str

