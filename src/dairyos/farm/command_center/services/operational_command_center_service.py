from dataclasses import asdict, is_dataclass
from datetime import datetime
import hashlib

from dairyos.farm.command_center.assemblers.operational_command_center_assembler import OperationalCommandCenterAssembler
from dairyos.farm.command_center.services.attention_queue_service import AttentionQueueService
from dairyos.farm.command_center.services.missing_input_detection_service import MissingInputDetectionService
from dairyos.farm.operations.state.operational_decision_service import OperationalDecisionService
from dairyos.operations.actions.services.operational_action_service import OperationalActionService
from dairyos.domain.events import Event
from dairyos.operations.actions.models.operational_action import OperationalAction
from dairyos.operations.actions.models.action_assignment import ActionAssignment
from dairyos.operations.actions.models.action_status import ActionStatus
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
                 operational_action_service=None,
                 event_publisher=None):
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
        self.event_publisher = event_publisher
        self.assembler = assembler or OperationalCommandCenterAssembler()
        self._decisions = {}
        self._decision_actions = {}
        self._published_decision_ids = set()

    def snapshot(self):
        state = self.operational_state_service.get_state()
        farm_state = state.summary()
        attention = self.attention_queue_service.build(farm_state=state)
        farm_state["attention_queue"] = [self._serialize(item) for item in attention]

        recommendations = self.operational_decision_service.evaluate()
        decision_payload = self._sync_decisions(recommendations)
        action_payload = self._sync_actions()

        active_decisions = len(decision_payload)
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

        self._publish_state_event(
            "operational_decision_acknowledged",
            {
                "decision_id": decision.decision_id,
                "owner": decision.owner,
                "status": decision.status,
                "acknowledged_at": (
                    decision.acknowledged_at.isoformat()
                    if decision.acknowledged_at
                    else None
                ),
            },
        )

        return self._serialize_decision(decision)

    def resolve_decision(self, decision_id, operator, outcome=None):
        decision = self._find_decision(decision_id)

        if decision.owner is None:
            decision.owner = operator

        decision.complete(
            outcome=outcome or "Resolved by operator"
        )

        self._publish_state_event(
            "operational_decision_completed",
            {
                "decision_id": decision.decision_id,
                "owner": decision.owner,
                "status": decision.status,
                "outcome": decision.outcome,
                "completed_at": (
                    decision.completed_at.isoformat()
                    if decision.completed_at
                    else None
                ),
            },
        )

        return self._serialize_decision(decision)

    def update_action(self, action_id, status, operator=None):
        action = next((item for item in self.operational_action_service.get_actions() if item.action_id == action_id), None)
        if action is None:
            raise KeyError(f"Unknown action: {action_id}")
        if operator:
            action.assignment.assigned_to = operator

        action.status.transition_to(
            status.upper()
        )

        self._publish_state_event(
            "operational_action_updated",
            {
                "action_id": action.action_id,
                "status": action.status.status,
                "assigned_to": action.assignment.assigned_to,
                "updated_at": (
                    action.status.updated_at.isoformat()
                    if action.status.updated_at
                    else None
                ),
            },
        )

        return self._serialize(action)


    def _publish_state_event(self, name, payload):
        """Persist command-center lifecycle state through the canonical journal."""
        if self.event_publisher is None:
            return

        self.event_publisher(
            Event(
                name=name,
                payload=dict(payload),
            )
        )

    def restore_from_events(self, events):
        """Reconstruct decisions/actions from durable command-center events."""
        self._decisions.clear()
        self._decision_actions.clear()
        self._published_decision_ids.clear()
        self.operational_action_service.actions.clear()

        for event in events or []:
            name = getattr(event, "name", None)
            payload = dict(getattr(event, "payload", None) or {})

            if name == "operational_decision_created":
                condition_key = self._condition_key_from_repr(
                    payload.get("condition_key")
                )

                if condition_key is None:
                    continue

                decision_payload = dict(
                    payload.get("decision") or {}
                )

                decision = self._decision_from_payload(
                    decision_payload
                )

                self._decisions[
                    condition_key
                ] = decision

                self._published_decision_ids.add(
                    decision.decision_id
                )

            elif name == "operational_decision_acknowledged":
                decision = self._find_decision_if_present(
                    payload.get("decision_id")
                )

                if decision is not None:
                    decision.status = payload.get(
                        "status",
                        decision.status,
                    )
                    decision.owner = payload.get(
                        "owner",
                        decision.owner,
                    )
                    decision.acknowledged_at = (
                        self._parse_datetime(
                            payload.get("acknowledged_at")
                        )
                    )

            elif name == "operational_decision_completed":
                decision = self._find_decision_if_present(
                    payload.get("decision_id")
                )

                if decision is not None:
                    decision.status = payload.get(
                        "status",
                        decision.status,
                    )
                    decision.owner = payload.get(
                        "owner",
                        decision.owner,
                    )
                    decision.outcome = payload.get(
                        "outcome",
                        decision.outcome,
                    )
                    decision.completed_at = (
                        self._parse_datetime(
                            payload.get("completed_at")
                        )
                    )

            elif name == "operational_action_created":
                condition_key = self._condition_key_from_repr(
                    payload.get("condition_key")
                )

                action_payload = dict(
                    payload.get("action") or {}
                )

                action = self._action_from_payload(
                    action_payload
                )

                self.operational_action_service.actions.append(
                    action
                )

                if condition_key is not None:
                    self._decision_actions[
                        condition_key
                    ] = action.action_id

            elif name == "operational_action_updated":
                action_id = payload.get("action_id")

                action = next(
                    (
                        item
                        for item
                        in self.operational_action_service.get_actions()
                        if item.action_id == action_id
                    ),
                    None,
                )

                if action is not None:
                    assigned_to = payload.get("assigned_to")

                    if assigned_to:
                        action.assignment.assigned_to = (
                            assigned_to
                        )

                    status = payload.get("status")

                    if status:
                        action.status.status = str(
                            status
                        ).upper()

                    updated_at = payload.get(
                        "updated_at"
                    )

                    if updated_at:
                        action.status.updated_at = (
                            self._parse_datetime(
                                updated_at
                            )
                        )

    def _find_decision_if_present(self, decision_id):
        for decision in self._decisions.values():
            if decision.decision_id == decision_id:
                return decision

        return None

    @staticmethod
    def _parse_datetime(value):
        if not value:
            return None

        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

    @staticmethod
    def _condition_key_from_repr(value):
        if not value:
            return None

        import ast

        parsed = ast.literal_eval(
            str(value)
        )

        return tuple(
            tuple(item)
            if isinstance(item, list)
            else item
            for item in parsed
        )

    @classmethod
    def _decision_from_payload(cls, payload):
        return OperationalDecision(
            decision_id=payload["decision_id"],
            title=payload["title"],
            description=payload["description"],
            priority=DecisionPriority(
                level=payload["priority"],
                score=float(
                    payload.get(
                        "priority_score",
                        0,
                    )
                ),
            ),
            owner_action_required=bool(
                payload.get(
                    "owner_action_required",
                    True,
                )
            ),
            status=payload.get(
                "status",
                "CREATED",
            ),
            owner=payload.get("owner"),
            source=payload.get("source"),
            outcome=payload.get("outcome"),
            created_at=cls._parse_datetime(
                payload.get("created_at")
            ) or datetime.now(),
            acknowledged_at=cls._parse_datetime(
                payload.get("acknowledged_at")
            ),
            completed_at=cls._parse_datetime(
                payload.get("completed_at")
            ),
        )

    @classmethod
    def _action_from_payload(cls, payload):
        assignment_payload = (
            payload.get("assignment") or {}
        )

        status_payload = (
            payload.get("status") or {}
        )

        return OperationalAction(
            action_id=payload["action_id"],
            title=payload["title"],
            description=payload["description"],
            assignment=ActionAssignment(
                assigned_to=str(
                    assignment_payload.get(
                        "assigned_to",
                        "",
                    )
                ),
                department=str(
                    assignment_payload.get(
                        "department",
                        "",
                    )
                ),
            ),
            status=ActionStatus(
                status=str(
                    status_payload.get(
                        "status",
                        "OPEN",
                    )
                ).upper()
            ),
            priority=str(
                payload.get(
                    "priority",
                    "NORMAL",
                )
            ).upper(),
            source_event_id=payload.get(
                "source_event_id"
            ),
            source_decision_id=payload.get(
                "source_decision_id"
            ),
            created_by_system=bool(
                payload.get(
                    "created_by_system",
                    True,
                )
            ),
            due_date=cls._parse_datetime(
                payload.get("due_date")
            ),
            created_at=cls._parse_datetime(
                payload.get("created_at")
            ) or datetime.now(),
        )

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
                decision = self._create_decision(
                    key,
                    recommendation,
                )
                self._decisions[key] = decision

            self._publish_decision_created(
                key,
                decision,
            )

            payload.append(
                self._serialize_decision(
                    decision
                )
            )

        return payload

    def _create_decision(self, key, recommendation):
        priority = str(recommendation.get("priority", "NORMAL")).upper()
        details = recommendation.get("details")
        description = self._describe(recommendation, details)
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
            if (
                not decision.owner_action_required
                or decision.status == "COMPLETED"
            ):
                continue

            # Guarantee that every decision converted into an operational
            # action has a durable creation event. This also covers callers
            # that populate _decisions directly before syncing actions.
            self._publish_decision_created(
                key,
                decision,
            )

            if key in self._decision_actions:
                continue

            role = self.ASSIGNMENT_ROLE.get(
                decision.source or "",
                "Farm Operator",
            )

            action = self.operational_action_service.create_action(
                title=decision.title,
                description=decision.description,
                assigned_to=role,
                department="Farm Operations",
                source_decision_id=decision.decision_id,
                priority=decision.priority.level,
            )

            self._decision_actions[key] = action.action_id

            self._publish_state_event(
                "operational_action_created",
                {
                    "condition_key": repr(key),
                    "action": self._serialize(action),
                },
            )

        return [
            self._serialize(item)
            for item in self.operational_action_service.get_actions()
        ]

    def _publish_decision_created(self, key, decision):
        decision_id = decision.decision_id

        if decision_id in self._published_decision_ids:
            return

        self._publish_state_event(
            "operational_decision_created",
            {
                "condition_key": repr(key),
                "decision": self._serialize_decision(
                    decision
                ),
            },
        )

        self._published_decision_ids.add(decision_id)

    @staticmethod
    def _describe(recommendation, details):
        """Render a human-readable, owner-facing description.

        `details` frequently arrives as a raw dict (a health observation, an
        exception payload, an inventory/financial signal). Falling back to
        `str(details)` produced Python dict reprs in the operator UI; this
        extracts the identifying fields instead so the persistent exception
        rail stays readable.
        """
        if isinstance(details, str) and details.strip():
            return details.strip()

        if isinstance(details, dict):
            animal_id = details.get("animal_id")
            label = (
                details.get("observation")
                or details.get("symptom")
                or details.get("message")
                or details.get("description")
                or details.get("inventory_type")
                or details.get("financial_id")
            )
            severity = details.get("severity")

            parts = []
            if animal_id:
                parts.append(f"Animal {animal_id}")
            if label:
                parts.append(str(label))
            if severity:
                parts.append(f"severity: {severity}")

            if parts:
                return " â€” ".join(parts)

        fallback = recommendation.get("title") or recommendation.get("action")
        return str(fallback or "Review operational condition")

    @staticmethod
    def _condition_key(recommendation):
        details = recommendation.get("details")
        if isinstance(details, dict):
            normalized = tuple(sorted((str(k), str(v)) for k, v in details.items() if k not in {"timestamp", "updated_at"}))
        else:
            normalized = str(details)
        return (str(recommendation.get("type")), str(recommendation.get("action")), str(recommendation.get("animal_id")), normalized)

    @classmethod
    def _serialize_decision(cls, decision):
        return cls._serialize(
            {
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
        )

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
