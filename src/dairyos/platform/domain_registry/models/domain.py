from dataclasses import dataclass


from dairyos.platform.domain_registry.models.domain_status import (
    DomainStatus,
)



@dataclass
class Domain:

    name: str

    owner: str

    version: str

    status: DomainStatus = DomainStatus.ACTIVE

