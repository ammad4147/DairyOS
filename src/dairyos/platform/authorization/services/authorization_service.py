from dairyos.platform.authorization.models.access_decision import (
    AccessDecision,
    AuthorizationResult,
)


class AuthorizationService:
    """
    Enterprise authorization decision service.
    """


    def __init__(self):

        self.permissions = {}



    def grant(
        self,
        subject: str,
        resource: str,
        action: str,
    ):

        key = (
            subject,
            resource,
            action,
        )

        self.permissions[key] = True



    def authorize(
        self,
        subject: str,
        resource: str,
        action: str,
    ):

        key = (
            subject,
            resource,
            action,
        )


        allowed = self.permissions.get(
            key,
            False,
        )


        return AuthorizationResult(

            decision=
                AccessDecision.ALLOW
                if allowed
                else AccessDecision.DENY,

            reason=
                "permission granted"
                if allowed
                else "permission denied",

            subject=subject,

            resource=resource,
        )
