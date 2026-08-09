from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.services.workforce_intelligence_service import (
    WorkforceIntelligenceService,
)

from dairyos.farm.operations.services.inventory_intelligence_service import (
    InventoryIntelligenceService,
)

from dairyos.farm.operations.services.equipment_intelligence_service import (
    EquipmentIntelligenceService,
)

from dairyos.farm.operations.services.financial_intelligence_service import (
    FinancialIntelligenceService,
)


class OperationalDecisionService:
    """
    Converts operational state into farm decisions.

    State answers:
        What is true?

    Decisions answer:
        What requires action?

    Rules:
    - Reads FarmOperationalState only.
    - Never modifies operational facts.
    - Produces recommended actions only.
    - Manual farm operations remain authoritative.
    - Escalation is rule-based awareness only.
    """


    def __init__(
        self,
        operational_state_service: FarmOperationalStateService,
        workforce_intelligence_service=None,
        inventory_intelligence_service=None,
        equipment_intelligence_service=None,
        financial_intelligence_service=None,
    ):

        self.operational_state_service = (
            operational_state_service
        )

        self.workforce_intelligence_service = (
            workforce_intelligence_service
            if workforce_intelligence_service is not None
            else WorkforceIntelligenceService()
        )

        self.inventory_intelligence_service = (
            inventory_intelligence_service
            if inventory_intelligence_service is not None
            else InventoryIntelligenceService()
        )

        self.equipment_intelligence_service = (
            equipment_intelligence_service
            if equipment_intelligence_service is not None
            else EquipmentIntelligenceService()
        )

        self.financial_intelligence_service = (
            financial_intelligence_service
            if financial_intelligence_service is not None
            else FinancialIntelligenceService()
        )


    def evaluate(
        self,
    ):

        state = (
            self.operational_state_service
            .get_state()
        )

        decisions = []

        seen = set()


        def add_decision(
            decision,
            source,
            escalation_level="NORMAL",
        ):

            decision["source"] = source

            decision["escalation_level"] = (
                escalation_level
            )

            fingerprint = (
                decision.get("type"),
                decision.get("action"),
                decision.get("animal_id"),
                str(
                    decision.get("details")
                ),
            )

            if fingerprint in seen:
                return

            seen.add(
                fingerprint
            )

            decisions.append(
                decision
            )


        for alert in state.health_alerts:

            severity = alert.get(
                "severity"
            )

            add_decision(
                {
                    "type": "health",
                    "priority":
                        self._health_priority(
                            severity
                        ),
                    "animal_id":
                        alert.get(
                            "animal_id"
                        ),
                    "action":
                        "review_health_observation",
                    "title":
                        "Review health observation",
                    "details":
                        alert,
                },
                source="health",
                escalation_level=(
                    "CRITICAL"
                    if severity in (
                        "critical",
                        "severe",
                    )
                    else "NORMAL"
                ),
            )


        for exception in state.exceptions:

            severity = exception.get(
                "severity",
                "HIGH",
            )

            add_decision(
                {
                    "type":
                        "operations",

                    "priority":
                        "critical"
                        if severity in (
                            "CRITICAL",
                            "critical",
                        )
                        else "high",

                    "action":
                        "review_exception",

                    "title":
                        "Review operational exception",

                    "details":
                        exception,
                },

                source="operations",

                escalation_level=(
                    severity.upper()
                ),
            )


        for task in state.open_tasks:

            add_decision(
                {
                    "type":
                        "task",

                    "priority":
                        "high",

                    "action":
                        "complete_operational_task",

                    "title":
                        "Complete open operational task",

                    "details":
                        task,
                },

                source="task",

                escalation_level="HIGH",
            )


        if state.schedule_state is not None:

            for notification in (
                state.schedule_state
                .evaluate_heads_up()
            ):

                add_decision(
                    {
                        "type":
                            "schedule",

                        "priority":
                            "high",

                        "action":
                            "complete_scheduled_activity",

                        "title":
                            "Complete scheduled activity",

                        "details":
                            notification,
                    },

                    source="schedule",

                    escalation_level="HIGH",
                )

        if not state.milk_status:

            add_decision(
                {
                    "type":
                        "production",

                    "priority":
                        "high",

                    "action":
                        "record_milk_activity",

                    "title":
                        "Complete milk production recording",

                    "details":
                        "No milk activity recorded",
                },

                source="production",

                escalation_level="HIGH",
            )



        if not state.feeding_status:

            add_decision(
                {
                    "type":
                        "feeding",

                    "priority":
                        "high",

                    "action":
                        "record_feed_activity",

                    "title":
                        "Complete feeding activity recording",

                    "details":
                        "No feeding activity recorded",
                },

                source="feeding",

                escalation_level="HIGH",
            )



        for inventory_decision in (
            self.inventory_intelligence_service
            .evaluate(
                state
            )
        ):

            add_decision(
                inventory_decision,
                source="inventory",
                escalation_level=(
                    inventory_decision.get(
                        "priority",
                        "NORMAL",
                    )
                ),
            )



        for workforce_decision in (
            self.workforce_intelligence_service
            .evaluate(
                state
            )
        ):

            add_decision(
                workforce_decision,
                source="workforce",
                escalation_level=(
                    workforce_decision.get(
                        "priority",
                        "NORMAL",
                    )
                ),
            )



        for equipment_decision in (
            self.equipment_intelligence_service
            .evaluate(
                state
            )
        ):

            add_decision(
                equipment_decision,
                source="equipment",
                escalation_level=(
                    equipment_decision.get(
                        "priority",
                        "NORMAL",
                    )
                ),
            )



        for financial_decision in (
            self.financial_intelligence_service
            .evaluate(
                state
            )
        ):

            add_decision(
                financial_decision,
                source="financial",
                escalation_level=(
                    financial_decision.get(
                        "priority",
                        "NORMAL",
                    )
                ),
            )



        return decisions


    def active_decisions(
        self,
    ):

        return self.evaluate()


    def count(
        self,
    ):

        return len(
            self.evaluate()
        )



    def priority_summary(
        self,
    ):

        summary = {
            "critical": 0,
            "high": 0,
            "normal": 0,
            "warning": 0,
        }


        for decision in (
            self.evaluate()
        ):

            priority = (
                decision.get(
                    "priority",
                    "normal",
                )
                .lower()
            )


            if priority in summary:

                summary[priority] += 1


        return summary



    def _health_priority(
        self,
        severity,
    ):

        if severity in (
            "critical",
            "severe",
        ):

            return "critical"


        return "normal"
