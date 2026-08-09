"""
DairyOS Executive API

Enterprise executive application boundary.

Responsibilities:

- execute executive runtime view
- expose executive command center
- expose executive intelligence facade
- provide owner-facing intelligence access

Does not contain intelligence logic.
"""


class ExecutiveAPI:
    """
    Application boundary for executive intelligence.
    """



    def __init__(
        self,
        runtime_service=None,
        facade=None,
    ):


        if runtime_service is None:

            from dairyos.intelligence.integration.executive_runtime_service import (
                ExecutiveRuntimeService,
            )

            runtime_service = ExecutiveRuntimeService()



        if facade is None:

            from dairyos.intelligence.application.executive_intelligence_facade import (
                ExecutiveIntelligenceFacade,
            )

            facade = ExecutiveIntelligenceFacade(
                runtime_service=runtime_service,
            )



        self.runtime_service = (
            runtime_service
        )


        self.facade = (
            facade
        )



    def execute(
        self,
        context=None,
    ):

        return (
            self.runtime_service
            .execute(
                context
            )
        )



    def execute_intelligence(
        self,
        context=None,
    ):

        return (
            self.facade
            .execute(
                context
            )
        )



    def get_command_center(
        self,
        context=None,
    ):

        result = self.execute(
            context
        )


        return result.get(
            "command_center"
        )



    def get_cockpit(
        self,
        context=None,
    ):

        result = self.execute(
            context
        )


        return result.get(
            "cockpit"
        )



    def get_decision(
        self,
        context=None,
    ):

        result = self.execute_intelligence(
            context
        )


        return result.get(
            "decision"
        )



    def get_report(
        self,
        context=None,
    ):

        result = self.execute_intelligence(
            context
        )


        return result.get(
            "report"
        )
