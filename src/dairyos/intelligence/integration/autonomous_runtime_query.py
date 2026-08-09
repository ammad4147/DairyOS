"""
DairyOS Autonomous Runtime Query

Read-only intelligence runtime inspection boundary.

Provides:

- cycle history access
- cycle replay lookup
- runtime status summary

Does not modify execution.
"""


class AutonomousRuntimeQuery:
    """
    Enterprise read boundary for autonomous runtime data.
    """


    def __init__(
        self,
        replay_service=None,
    ):

        if replay_service is None:

            from dairyos.intelligence.integration.autonomous_replay_service import (
                AutonomousReplayService,
            )

            replay_service = AutonomousReplayService()


        self.replay_service = replay_service



    def get_cycle_history(
        self,
    ):

        return (
            self.replay_service
            .get_autonomous_cycles()
        )



    def get_cycle(
        self,
        cycle_id: str,
    ):

        return (
            self.replay_service
            .replay_cycle(
                cycle_id
            )
        )



    def get_status(
        self,
    ):

        cycles = self.get_cycle_history()


        return {
            "component": "autonomous_runtime_query",
            "status": "operational",
            "cycle_count": len(
                cycles
            ),
        }
