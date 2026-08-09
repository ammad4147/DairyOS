class EscalationRuleService:
    """
    Defines escalation decisions.
    """


    def determine_level(
        self,
        delay_hours: int,
    ):

        if delay_hours >= 24:

            return "LEVEL_THREE"


        if delay_hours >= 8:

            return "LEVEL_TWO"


        return "LEVEL_ONE"
