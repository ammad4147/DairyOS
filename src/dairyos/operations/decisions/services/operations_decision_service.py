from typing import List

from ..models.operational_decision import OperationalDecision
from ..models.decision_priority import DecisionPriority
from ..models.decision_context import DecisionContext

from dairyos.runtime.persistent_event_journal import (
    PersistentEventJournal,
)

from ..events.decision_events import (
    DecisionEvents,
)


class OperationsDecisionService:
    """
    Converts operational situations into recommended decisions.

    Responsibilities:
    - create decisions
    - track decision lifecycle
    - publish decision events

    Does not:
    - execute farm actions
    - mutate operational state
    """


    def __init__(
        self,
        event_journal: PersistentEventJournal | None = None,
    ):

        self.decisions: List[OperationalDecision] = []

        self.event_journal = (
            event_journal
            if event_journal is not None
            else PersistentEventJournal()
        )



    def create_decision(
        self,
        context: DecisionContext,
        priority: str = "MEDIUM",
        owner_action_required: bool = False,
    ) -> OperationalDecision:


        score = {

            "CRITICAL": 100,
            "HIGH": 75,
            "MEDIUM": 50,
            "LOW": 25,

        }.get(

            priority.upper(),

            50,

        )


        decision = OperationalDecision(

            decision_id=(
                f"DEC-{len(self.decisions)+1:04d}"
            ),

            title=context.category,

            description=context.description,

            priority=DecisionPriority(

                level=priority.upper(),

                score=score,

            ),

            owner_action_required=(
                owner_action_required
            ),

            source=context.source,

        )


        self.decisions.append(
            decision
        )


        self.event_journal.append(

            DecisionEvents.created(
                decision
            )

        )


        return decision



    def get_decisions(
        self,
    ) -> List[OperationalDecision]:

        return self.decisions



    def get_decision(
        self,
        decision_id: str,
    ) -> OperationalDecision | None:


        for decision in self.decisions:

            if decision.decision_id == decision_id:

                return decision


        return None



    def acknowledge_decision(
        self,
        decision_id: str,
        owner: str | None = None,
    ) -> OperationalDecision | None:


        decision = self.get_decision(
            decision_id
        )


        if decision is None:

            return None


        decision.acknowledge(
            owner=owner
        )


        self.event_journal.append(

            DecisionEvents.acknowledged(
                decision
            )

        )


        return decision



    def complete_decision(
        self,
        decision_id: str,
        outcome: str | None = None,
    ) -> OperationalDecision | None:


        decision = self.get_decision(
            decision_id
        )


        if decision is None:

            return None


        decision.complete(
            outcome=outcome
        )


        self.event_journal.append(

            DecisionEvents.completed(
                decision
            )

        )


        return decision



    def active_decisions(
        self,
    ) -> List[OperationalDecision]:

        return [

            decision

            for decision in self.decisions

            if decision.status != "COMPLETED"

        ]
