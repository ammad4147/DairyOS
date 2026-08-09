"""
DairyOS Autonomous Intelligence Application Service

Application-facing boundary for autonomous intelligence.

Coordinates:

- runtime execution
- runtime queries
- status reporting

Does not contain intelligence decision logic.
"""


class AutonomousIntelligenceService:
    """
    Application service for autonomous intelligence operations.
    """


    def __init__(
        self,
        runtime_session=None,
        runtime_query=None,
    ):

        if runtime_session is None:

            from dairyos.intelligence.integration.autonomous_runtime_session import (
                AutonomousRuntimeSession,
            )

            runtime_session = AutonomousRuntimeSession()


        if runtime_query is None:

            from dairyos.intelligence.integration.autonomous_runtime_query import (
                AutonomousRuntimeQuery,
            )

            runtime_query = AutonomousRuntimeQuery()


        self.runtime_session = runtime_session

        self.runtime_query = runtime_query



    def execute_cycle(
        self,
        context=None,
    ):

        return self.runtime_session.execute(
            context
        )



    def get_cycle_history(
        self,
    ):

        return self.runtime_query.get_cycle_history()



    def get_cycle(
        self,
        cycle_id: str,
    ):

        return self.runtime_query.get_cycle(
            cycle_id
        )



    def get_runtime_status(
        self,
    ):

        return self.runtime_query.get_status()
