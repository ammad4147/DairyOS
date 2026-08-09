from typing import Any


class CommandCenterService:
    """
    Application dashboard command-center read service.

    Read-only presentation boundary.

    The operational command-center service remains responsible for
    assembling the current operational picture. This service exposes
    that picture to the dashboard layer without creating another
    application graph or introducing business logic.
    """

    def __init__(
        self,
        command_center_projection: Any | None = None,
        operational_command_center_service: Any | None = None,
    ):
        self.command_center_projection = (
            command_center_projection
        )

        self.operational_command_center_service = (
            operational_command_center_service
        )

    def get_snapshot(self):
        """
        Return the owner-facing command-center snapshot.

        Preferred source:
            OperationalCommandCenterService

        Compatibility source:
            CommandCenterProjectionService exposing build_snapshot()

        The returned shape remains stable for the dashboard:
            {
                "system": "DairyOS",
                "command_center": {...},
            }
        """

        if (
            self.operational_command_center_service
            is not None
        ):
            snapshot = (
                self.operational_command_center_service
                .get_snapshot()
            )

            return {
                "system": "DairyOS",
                "command_center": snapshot,
            }

        if self.command_center_projection is not None:

            if hasattr(
                self.command_center_projection,
                "build_snapshot",
            ):
                snapshot = (
                    self.command_center_projection
                    .build_snapshot()
                )

                return {
                    "system": "DairyOS",
                    "command_center": snapshot,
                }

            if hasattr(
                self.command_center_projection,
                "build_view",
            ):
                snapshot = (
                    self.command_center_projection
                    .build_view()
                )

                return {
                    "system": "DairyOS",
                    "command_center": snapshot,
                }

            if hasattr(
                self.command_center_projection,
                "project",
            ):
                snapshot = (
                    self.command_center_projection
                    .project()
                )

                return {
                    "system": "DairyOS",
                    "command_center": snapshot,
                }

        return {
            "system": "DairyOS",
            "command_center": {
                "status": "UNAVAILABLE",
                "attention_required": False,
            },
        }
