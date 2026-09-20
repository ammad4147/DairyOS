from datetime import UTC, datetime
from typing import Any

from dairyos.operations.alerts.models.alert_severity import (
    AlertSeverity,
)
from dairyos.operations.alerts.models.operational_alert import (
    OperationalAlert,
)
from dairyos.operations.alerts.services.alert_management_service import (
    AlertManagementService,
)
from dairyos.operations.decisions.models.decision_context import (
    DecisionContext,
)
from dairyos.operations.decisions.services.operations_decision_service import (
    OperationsDecisionService,
)
from dairyos.operations.escalation.models.escalation_level import (
    EscalationLevel,
)
from dairyos.operations.escalation.models.operational_escalation import (
    OperationalEscalation,
)
from dairyos.operations.escalation.services.escalation_management_service import (
    EscalationManagementService,
)
from dairyos.operations.escalation.services.escalation_rule_service import (
    EscalationRuleService,
)
from dairyos.operations.intelligence.models.operational_signal import (
    OperationalSignal,
)


class OperationalResponseBridge:
    """
    Converts operational intelligence signals into
    decisions, alerts, and escalations.
    """

    def __init__(self):

        self.decision_service = (
            OperationsDecisionService()
        )

        self.alert_service = (
            AlertManagementService()
        )

        self.escalation_rule_service = (
            EscalationRuleService()
        )

        self.escalation_service = (
            EscalationManagementService()
        )


    def process_signal(
        self,
        signal: OperationalSignal,
        delay_hours: int = 0,
    ) -> dict[str, Any]:

        priority = self._map_priority(
            signal.severity
        )


        decision = self.decision_service.create_decision(
            context=DecisionContext(
                source=signal.source,
                category=signal.category,
                description=signal.description,
                operational_impact=signal.severity,
            ),
            priority=priority,
            owner_action_required=(
                priority in [
                    "HIGH",
                    "CRITICAL",
                ]
            ),
        )


        alert = OperationalAlert(

            alert_id=(
                f"ALT-{len(self.alert_service.alerts)+1:04d}"
            ),

            title=signal.category,

            severity=(
                self._map_alert_severity(
                    signal.severity
                )
            ),

            description=signal.description,

            created_at=datetime.now(
                UTC
            ),
        )


        self.alert_service.create_alert(
            alert
        )


        escalation = None


        if priority in [
            "HIGH",
            "CRITICAL",
        ]:

            level = (
                self.escalation_rule_service
                .determine_level(
                    delay_hours
                )
            )


            escalation = OperationalEscalation(

                escalation_id=(
                    f"ESC-{len(self.escalation_service.escalations)+1:04d}"
                ),

                issue_reference=(
                    alert.alert_id
                ),

                level=(
                    EscalationLevel[level]
                ),

                assigned_to=(
                    self._assign_owner(level)
                ),

                created_at=datetime.now(
                    UTC
                ),
            )


            self.escalation_service.create_escalation(
                escalation
            )


        return {

            "signal": signal,

            "decision": decision,

            "alert": alert,

            "escalation": escalation,

        }



    def _map_priority(
        self,
        severity: str,
    ) -> str:

        mapping = {

            "CRITICAL": "CRITICAL",

            "HIGH": "HIGH",

            "WARNING": "MEDIUM",

            "INFO": "LOW",

        }

        return mapping.get(
            severity.upper(),
            "MEDIUM",
        )



    def _map_alert_severity(
        self,
        severity: str,
    ) -> AlertSeverity:

        mapping = {

            "CRITICAL": AlertSeverity.CRITICAL,

            "HIGH": AlertSeverity.WARNING,

            "WARNING": AlertSeverity.WARNING,

            "INFO": AlertSeverity.INFO,

        }

        return mapping.get(
            severity.upper(),
            AlertSeverity.INFO,
        )



    def _assign_owner(
        self,
        level: str,
    ) -> str:

        mapping = {

            "LEVEL_ONE": "Farm Supervisor",

            "LEVEL_TWO": "Farm Manager",

            "LEVEL_THREE": "Farm Owner",

        }

        return mapping.get(
            level,
            "Farm Supervisor",
        )
