from dataclasses import dataclass, field


@dataclass
class AccessPolicy:
    """
    Defines a platform authorization rule.
    """

    resource: str

    action: str

    required_permissions: list[str] = field(
        default_factory=list
    )

    def allows(
        self,
        permissions: list[str]
    ) -> bool:

        return all(
            permission in permissions
            for permission in self.required_permissions
        )
