class KnowledgeRuleRepository:
    """
    Repository interface for intelligence rules.
    """


    def save(
        self,
        rule,
    ):

        raise NotImplementedError


    def get_all(
        self,
    ):

        raise NotImplementedError
