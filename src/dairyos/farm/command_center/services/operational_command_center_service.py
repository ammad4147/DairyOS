from dataclasses import asdict, is_dataclass
from datetime import datetime
import hashlib

from dairyos.farm.command_center.assemblers.operational_command_center_assembler import OperationalCommandCenterAssembler
from dairyos.farm.command_center.services.attention_queue_service import AttentionQueueService
from dairyos.farm.command_center.services.missing_input_detection_service import MissingInputDetectionService
from dairyos.farm.operations.state.operational_decision_service import OperationalDecisionService
from dairyos.operations.actions.services.operational_action_service import OperationalActionService
from dairyos.operations.decisions.models.operational_decision import OperationalDecision
from dairyos.operations.decisions.models.decision_priority import DecisionPriority


class OperationalCommandCenterService:
    """Build the operator-facing intelligence chain from canonical farm state."""

    PRIORITY_SCORE = {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 50, "LOW": 25, "NORMAL": 0}

    ASSIGNMENT_ROLE = {
        "health": "Veterinarian",
        "production": "Milking Supervisor",
        "feeding": "Feed Supervisor",
        "workforce": "Farm Manager",
        "inventory": "Feed Supervisor",
        "equipment": "Maintenance Lead",
        "financial": "Farm Manager",
        "operations": "Farm Manager",
        "schedule": "Farm Manager",
        "task": "Farm Manager",
    }

    def __init__(self, *, operational_state_service, operations_health_service,
                 assembler=None, attention_queue_service=None,
                 missing_input_detection_service=None,
                 operational_decision_service=None,
                 operational_action_service=None):
        self.operational_state_service = operational_state_service
        self.operations_health_service = operations_health_service
        self.missing_input_detection_service = missing_input_detection_service or MissingInputDetectionService()
        self.attention_queue_service = attention_queue_service or AttentionQueueService(
            missing_input_detection_service=self.missing_input_detection_service
        )
        self.operational_decision_service = operational_decision_service or OperationalDecisionService(
            operational_state_service=operational_state_service,
        )
        self.operational_action_service = operational_action_service or OperationalActionService()
        self.assembler = assembler or OperationalCommandCenterAssembler()
        self._decisions = {}
        self._decision_actions = {}

    def snapshot(self):
        state = self.operational_state_service.get_state()
        farm_state = state.summary()
        attention = self.attention_queue_service.build(farm_state=state)
        farm_state["attention_queue"] = [self._serialize(item) for item in attention]

        recommendations = self.operational_decision_service.evaluate()
        decision_payload = self._sync_decisions(recommendations)
        action_payload = self._sync_actions()

        active_decisions = sum(1 for item in self._decisions.values() if item.status != "COMPLETED")
        open_actions = sum(
            1 for item in self.operational_action_service.get_actions()
            if item.status.status not in {"CLOSED", "VERIFIED"}
        )

        health = self.operations_health_service.generate_snapshot(
            operational_score=None,
            active_decisions=active_decisions,
            pending_actions=open_actions,
            operational_state=state,
            attention_items=attention,
            decisions=recommendations,
        )

        return self.assembler.assemble(
            farm_state=farm_state,
            health={
                "health_status": health.health_status,
                "operational_score": health.operational_score,
                "active_decisions": health.active_decisions,
                "pending_actions": health.pending_actions,
                "tracked_outcomes": health.tracked_outcomes,
                "learning_signals": health.learning_signals,
                "owner_attention_required": health.owner_attention_required,
            },
            dashboard={},
            notifications=[],
            decisions={"items": decision_payload, "count": len(decision_payload), "active": active_decisions},
            execution={"actions": action_payload, "count": len(action_payload), "open": open_actions},
            intelligence={
                "attention_count": len(farm_state["attention_queue"]),
                "decision_count": len(decision_payload),
                "action_count": len(action_payload),
            },
        )

    def get_snapshot(self):
        return self.snapshot()

    def acknowledge_decision(self, decision_id, operator):
        decision = self._find_decision(decision_id)
        decision.acknowledge(owner=operator)
        return self._serialize_decision(decision)

    def resolve_decision(self, decision_id, operator, outcome=None):
        decision = self._find_decision(decision_id)
        if decision.owner is None:
            decision.owner = operator
        decision.complete(outcome=outcome or "Resolved by operator")
        return self._serialize_decision(decision)

    def update_action(self, action_id, status, operator=None):
        action = next((item for item in self.operational_action_service.get_actions() if item.action_id == action_id), None)
        if action is None:
            raise KeyError(f"Unknown action: {action_id}")
        if operator:
            action.assignment.assigned_to = operator
        action.status.transition_to(status.upper())
        return self._serialize(action)

    def _find_decision(self, decision_id):
        for decision in self._decisions.values():
            if decision.decision_id == decision_id:
                return decision
        raise KeyError(f"Unknown decision: {decision_id}")

    def _sync_decisions(self, recommendations):
        payload = []
        for recommendation in recommendations:
            key = self._condition_key(recommendation)
            decision = self._decisions.get(key)
            if decision is None:
                decision = self._create_decision(key, recommendation)
                self._decisions[key] = decision
            payload.append(self._serialize_decision(decision))
        return payload

    def _create_decision(self, key, recommendation):
        priority = str(recommendation.get("priority", "NORMAL")).upper()
        details = recommendation.get("details")
        description = details if isinstance(details, str) else str(details or recommendation.get("action", "Review operational condition"))
        decision_id = "DEC-" + hashlib.sha1(repr(key).encode("utf-8")).hexdigest()[:10].upper()
        return OperationalDecision(
            decision_id=decision_id,
            title=recommendation.get("title", "Review operational condition"),
            description=description,
            priority=DecisionPriority(level=priority, score=self.PRIORITY_SCORE.get(priority, 0)),
            owner_action_required=bool(recommendation.get("owner_action_required", True)),
            source=recommendation.get("source"),
        )

    def _sync_actions(self):
        for key, decision in self._decisions.items():
            if not decision.owner_action_required or decision.status == "COMPLETED" or key in self._decision_actions:
                continue
            role = self.ASSIGNMENT_ROLE.get(decision.source or "", "Farm Operator")
            action = self.operational_action_service.create_action(
                title=decision.title,
                description=decision.description,
                assigned_to=role,
                department="Farm Operations",
                source_decision_id=decision.decision_id,
                priority=decision.priority.level,
            )
            self._decision_actions[key] = action.action_id
        return [self._serialize(item) for item in self.operational_action_service.get_actions()]

    @staticmethod
    def _condition_key(recommendation):
        details = recommendation.get("details")
        if isinstance(details, dict):
            normalized = tuple(sorted((str(k), str(v)) for k, v in details.items() if k not in {"timestamp", "updated_at"}))
        else:
            normalized = str(details)
        return (str(recommendation.get("type")), str(recommendation.get("action")), str(recommendation.get("animal_id")), normalized)

    @staticmethod
    def _serialize_decision(decision):
        return {
            "decision_id": decision.decision_id,
            "title": decision.title,
            "description": decision.description,
            "priority": decision.priority.level,
            "priority_score": decision.priority.score,
            "owner_action_required": decision.owner_action_required,
            "status": decision.status,
            "owner": decision.owner,
            "source": decision.source,
            "outcome": decision.outcome,
            "created_at": decision.created_at,
            "acknowledged_at": decision.acknowledged_at,
            "completed_at": decision.completed_at,
        }

    @classmethod
    def _serialize(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        if is_dataclass(value):
            return cls._serialize(asdict(value))
        if isinstance(value, dict):
            return {key: cls._serialize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._serialize(item) for item in value]
        return value
