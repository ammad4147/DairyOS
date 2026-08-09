from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass
class OperationalDecision:
    """
    Operational recommendation generated
    from FarmOperationalState.

    Decisions are recommendations only.

    They do not modify operational truth.
    """


    type: str

    priority: str

    action: str

    title: str

    source: str

    escalation_level: str

    details: dict | str | None = None


    decision_id: str = field(
        default_factory=lambda: str(uuid4())
    )


    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )



    @classmethod
    def from_dict(
        cls,
        data,
    ):

        return cls(

            decision_id=data.get(
                "decision_id",
                str(uuid4()),
            ),

            type=data.get(
                "type",
                "unknown",
            ),

            priority=data.get(
                "priority",
                "normal",
            ),

            action=data.get(
                "action",
                "",
            ),

            title=data.get(
                "title",
                "",
            ),

            source=data.get(
                "source",
                "",
            ),

            escalation_level=data.get(
                "escalation_level",
                "NORMAL",
            ),

            details=data.get(
                "details",
            ),

            created_at=(
                datetime.fromisoformat(
                    data["created_at"]
                )
                if data.get("created_at")
                else datetime.now(UTC)
            ),

        )



    def to_dict(
        self,
    ):

        return {

            "decision_id":
                self.decision_id,

            "type":
                self.type,

            "priority":
                self.priority,

            "action":
                self.action,

            "title":
                self.title,

            "source":
                self.source,

            "escalation_level":
                self.escalation_level,

            "details":
                self.details,

            "created_at":
                self.created_at.isoformat(),

        }
