from dairyos.intelligence.knowledge.models.knowledge_rule import (
    KnowledgeRule,
)


class RuleGenerationService:
    """
    Generates intelligence rules.

    Future extensions:

    - automated policy generation
    - rule optimization
    """


    def generate(
        self,
        domain: str,
        condition: str,
        action: str,
        confidence: float,
    ) -> KnowledgeRule:

        return KnowledgeRule(
            domain=domain,
            condition=condition,
            action=action,
            confidence=confidence,
        )
