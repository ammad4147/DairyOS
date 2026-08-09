"""
DairyOS Command Gateway

Enterprise command access boundary.
"""


class CommandGateway:

    def __init__(self, orchestrator=None):

        if orchestrator is None:
            from dairyos.intelligence.command.services.command_orchestrator import (
                CommandOrchestrator,
            )

            orchestrator = CommandOrchestrator(
                None,
                None,
                None,
            )

        self.orchestrator = orchestrator

    def dispatch(self, command=None):

        if hasattr(self.orchestrator, "execute"):
            return self.orchestrator.execute(command)

        return None
