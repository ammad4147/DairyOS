from dairyos.farm.command_center.assemblers.command_center_projection_assembler import (
    CommandCenterProjectionAssembler,
)


class CommandCenterProjectionService:
    """
    Provides the owner-facing Command Center view.

    This service performs presentation projection only.
    It owns no operational decisions.
    """

    def __init__(
        self,
        *,
        assembler=None,
    ):

        self.assembler = (
            assembler
            or CommandCenterProjectionAssembler()
        )

    def project(
        self,
        *,
        command_center,
    ):

        return self.assembler.assemble(
            command_center=command_center
        )

    def build_view(
        self,
        *,
        operational_command_center,
    ):

        return self.project(
            command_center=operational_command_center
        )
