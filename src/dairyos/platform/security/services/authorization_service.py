from ..models.security_context import SecurityContext
from ..models.access_policy import AccessPolicy


class AuthorizationService:
    """
    Enterprise authorization decision service.
    """

    def __init__(self):
        self._policies: list[AccessPolicy] = []

    def register_policy(
        self,
        policy: AccessPolicy
    ) -> None:

        self._policies.append(policy)

    def authorize(
        self,
        context: SecurityContext,
        resource: str,
        action: str
    ) -> bool:

        matching = [
            policy
            for policy in self._policies
            if (
                policy.resource == resource
                and policy.action == action
            )
        ]

        if not matching:
            return False

        return any(
            policy.allows(
                context.permissions
            )
            for policy in matching
        )
