from dairyos.intelligence.knowledge.repository.knowledge_rule_repository import (
    KnowledgeRuleRepository,
)


class MemoryKnowledgeRuleRepository(
    KnowledgeRuleRepository,
):

    def __init__(
        self,
    ):

        self._items = []


    def save(
        self,
        rule,
    ):

        self._items.append(
            rule
        )


    def get_all(
        self,
    ):

        return self._items
