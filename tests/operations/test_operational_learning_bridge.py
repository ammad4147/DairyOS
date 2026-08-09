from datetime import datetime, timezone


from dairyos.operations.learning.services.operational_learning_bridge import (
    OperationalLearningBridge,
)

from dairyos.operations.outcomes.models.operational_outcome import (
    OperationalOutcome,
)

from dairyos.operations.outcomes.models.outcome_rating import (
    OutcomeRating,
)

from dairyos.operations.outcomes.models.outcome_feedback import (
    OutcomeFeedback,
)



def create_outcome(
    outcome_id="OUT-001",
    rating="HIGH",
):

    return OperationalOutcome(

        outcome_id=outcome_id,

        action_id="ACTION-001",

        result=(
            "Feed response improved after corrective action"
        ),

        rating=OutcomeRating(
            rating=rating,
        ),

        feedback=OutcomeFeedback(

            what_worked=(
                "Corrective feed action improved response"
            ),

            what_failed=(
                "Initial feed response was below target"
            ),

            improvement=(
                "Maintain corrective feeding protocol"
            ),

        ),

        created_at=datetime.now(
            timezone.utc
        ),

    )



def test_operational_learning_creates_learning_signal():

    bridge = OperationalLearningBridge()

    result = (
        bridge.process_outcome(
            create_outcome()
        )
    )


    assert (
        result["learning_signal"].signal_id
        == "SIG-OUT-001"
    )


    assert (
        len(
            bridge.learning_service.get_signals()
        )
        == 1
    )



def test_operational_learning_detects_pattern():

    bridge = OperationalLearningBridge()


    bridge.process_outcome(
        create_outcome(
            outcome_id="OUT-001"
        )
    )


    result = (
        bridge.process_outcome(
            create_outcome(
                outcome_id="OUT-002"
            )
        )
    )


    assert (
        len(result["patterns"])
        == 1
    )


    assert (
        result["patterns"][0]
        .occurrence_count
        == 2
    )



def test_operational_learning_creates_improvement():

    bridge = OperationalLearningBridge()


    bridge.process_outcome(
        create_outcome(
            outcome_id="OUT-001"
        )
    )


    result = (
        bridge.process_outcome(
            create_outcome(
                outcome_id="OUT-002"
            )
        )
    )


    assert (
        len(
            result[
                "improvement_opportunities"
            ]
        )
        == 1
    )


    assert (
        result[
            "improvement_opportunities"
        ][0]
        .related_pattern_id
        .startswith("PAT-")
    )



def test_operational_learning_stores_memory():

    bridge = OperationalLearningBridge()


    bridge.process_outcome(
        create_outcome(
            outcome_id="OUT-001"
        )
    )


    result = (
        bridge.process_outcome(
            create_outcome(
                outcome_id="OUT-002"
            )
        )
    )


    assert (
        len(
            result[
                "operational_memories"
            ]
        )
        == 1
    )


    assert (
        len(
            bridge.memory_service.get_all()
        )
        == 1
    )
