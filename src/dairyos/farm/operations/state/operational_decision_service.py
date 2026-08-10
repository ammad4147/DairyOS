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
from dairyos.farm.command_center.services.missing_input_detection_service import (
    MissingInputDetectionService,
)


class OperationalDecisionService:
    """Convert canonical FarmOperationalState into unique action-required decisions."""

    def __init__(
        self,
        operational_state_service,
        workforce_intelligence_service=None,
        inventory_intelligence_service=None,
        equipment_intelligence_service=None,
        financial_intelligence_service=None,
        missing_input_detection_service=None,
    ):
        self.operational_state_service = operational_state_service
        self.workforce_intelligence_service = workforce_intelligence_service or WorkforceIntelligenceService()
        self.inventory_intelligence_service = inventory_intelligence_service or InventoryIntelligenceService()
        self.equipment_intelligence_service = equipment_intelligence_service or EquipmentIntelligenceService()
        self.financial_intelligence_service = financial_intelligence_service or FinancialIntelligenceService()
        self.missing_input_detection_service = missing_input_detection_service or MissingInputDetectionService()

    def evaluate(self):
        state = self.operational_state_service.get_state()
        decisions = []
        seen = set()

        def add_decision(decision, source, escalation_level="NORMAL"):
            decision = dict(decision)
            decision["source"] = source
            decision["escalation_level"] = str(escalation_level).upper()
            decision.setdefault("owner_action_required", True)
            fingerprint = self._fingerprint(decision)
            if fingerprint in seen:
                return
            seen.add(fingerprint)
            decisions.append(decision)

        health_records = (getattr(state, "health_state", {}) or {}).values()
        if not health_records:
            health_records = self._latest_health_records(getattr(state, "health_alerts", []) or [])

        for alert in health_records:
            severity = str(alert.get("severity", "NORMAL")).upper()
            priority = self._health_priority(severity)
            if priority == "normal":
                continue
            add_decision(
                {
                    "type": "health",
                    "priority": priority,
                    "animal_id": alert.get("animal_id"),
                    "action": "review_health_observation",
                    "title": "Review health observation",
                    "details": alert,
                },
                source="health",
                escalation_level=priority,
            )

        for exception in getattr(state, "exceptions", []) or []:
            severity = str(exception.get("severity", "HIGH")).upper()
            priority = "critical" if severity == "CRITICAL" else "high"
            add_decision(
                {
                    "type": "operations",
                    "priority": priority,
                    "action": "review_exception",
                    "title": "Review operational exception",
                    "details": exception,
                },
                source="operations",
                escalation_level=severity,
            )

        for task in getattr(state, "open_tasks", []) or []:
            add_decision(
                {
                    "type": "task",
                    "priority": "high",
                    "action": "complete_operational_task",
                    "title": "Complete open operational task",
                    "details": task,
                },
                source="task",
                escalation_level="HIGH",
            )

        if getattr(state, "schedule_state", None) is not None:
            for notification in state.schedule_state.evaluate_heads_up():
                add_decision(
                    {
                        "type": "schedule",
                        "priority": "high",
                        "action": "complete_scheduled_activity",
                        "title": "Complete scheduled activity",
                        "details": notification,
                    },
                    source="schedule",
                    escalation_level="HIGH",
                )

        for gap in self.missing_input_detection_service.detect(state):
            action_map = {
                "MILK": ("production", "record_milk_activity", "Complete milk production recording"),
                "FEEDING": ("feeding", "record_feed_activity", "Complete feeding activity recording"),
                "WORKFORCE": ("workforce", "record_workforce_activity", "Complete workforce activity recording"),
            }
            decision_type, action, title = action_map.get(
                gap.area,
                (str(gap.area).lower(), "record_operational_activity", f"Resolve {gap.area} input gap"),
            )
            add_decision(
                {
                    "type": decision_type,
                    "priority": str(gap.severity).lower(),
                    "action": action,
                    "title": title,
                    "details": {
                        "area": gap.area,
                        "message": gap.message,
                        "expected_activity": gap.expected_activity,
                    },
                },
                source="missing_input",
                escalation_level=str(gap.severity).upper(),
            )

        for service, source in (
            (self.inventory_intelligence_service, "inventory"),
            (self.workforce_intelligence_service, "workforce"),
            (self.equipment_intelligence_service, "equipment"),
            (self.financial_intelligence_service, "financial"),
        ):
            for decision in service.evaluate(state):
                add_decision(
                    decision,
                    source=source,
                    escalation_level=decision.get("priority", "NORMAL"),
                )

        return decisions

    def active_decisions(self):
        return self.evaluate()

    def count(self):
        return len(self.evaluate())

    def priority_summary(self):
        summary = {"critical": 0, "high": 0, "medium": 0, "normal": 0, "low": 0, "warning": 0}
        for decision in self.evaluate():
            priority = str(decision.get("priority", "normal")).lower()
            if priority in summary:
                summary[priority] += 1
        return summary

    @staticmethod
    def _health_priority(severity):
        return {
            "CRITICAL": "critical",
            "SEVERE": "high",
            "HIGH": "high",
            "ELEVATED": "medium",
            "WARNING": "medium",
            "MEDIUM": "medium",
            "LOW": "low",
        }.get(str(severity).upper(), "normal")

    @staticmethod
    def _latest_health_records(records):
        latest = {}
        for record in records:
            key = record.get("animal_id") or "__farm__"
            previous = latest.get(key)
            if previous is None or str(record.get("timestamp")) > str(previous.get("timestamp")):
                latest[key] = record
        return list(latest.values())

    @staticmethod
    def _fingerprint(decision):
        details = decision.get("details")
        if isinstance(details, dict):
            details_key = tuple(
                sorted(
                    (str(k), str(v))
                    for k, v in details.items()
                    if k not in {"timestamp", "updated_at"}
                )
            )
        else:
            details_key = str(details)
        return (
            str(decision.get("type")),
            str(decision.get("action")),
            str(decision.get("animal_id")),
            details_key,
        )
