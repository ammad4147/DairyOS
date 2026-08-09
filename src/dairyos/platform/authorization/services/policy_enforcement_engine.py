from dairyos.platform.authorization.models.access_decision import (
    AccessDecision,
    AuthorizationResult,
)


class PolicyEnforcementEngine:
    """
    Central enterprise authorization enforcement point.
    """


    def __init__(
        self,
        authorization_service,
        governance_service=None,
        audit_service=None,
    ):

        self.authorization_service = authorization_service

        self.governance_service = governance_service

        self.audit_service = audit_service



    def evaluate(
        self,
        subject: str,
        resource: str,
        action: str,
    ):


        authorization = (
            self.authorization_service.authorize(
                subject,
                resource,
                action,
            )
        )


        result = authorization



        if (
            self.governance_service
            and result.decision == AccessDecision.ALLOW
        ):

            policies = (
                self.governance_service.list_policies()
            )


            if not policies:

                result = AuthorizationResult(

                    decision=AccessDecision.DENY,

                    reason="No governance policy registered",

                    subject=subject,

                    resource=resource,
                )



        if self.audit_service:

            self.audit_service.record(

                "authorization_decision",

                {
                    "subject": subject,
                    "resource": resource,
                    "action": action,
                    "decision": result.decision.value,
                }
            )


        return result
