from dairyos.intelligence.decision.repository.adapters import (
    MemoryDecisionRepository,
)

from dairyos.intelligence.decision.models import (
    DecisionRecommendation,
)



def test_memory_decision_repository_save():

    repository = MemoryDecisionRepository()


    decision = DecisionRecommendation(
        category="operational_risk",
        recommendation="Review conditions",
        rationale="Risk detected",
        confidence=0.8,
        priority="high",
    )


    repository.save(
        decision
    )


    results = repository.get_all()


    assert len(results) == 1

    assert results[0].category == (
        "operational_risk"
    )



def test_memory_decision_repository_empty():

    repository = MemoryDecisionRepository()


    results = repository.get_all()


    assert results == []
