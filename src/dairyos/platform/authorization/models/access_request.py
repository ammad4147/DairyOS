from dataclasses import dataclass


@dataclass
class AccessRequest:

    subject: str

    resource: str

    action: str
