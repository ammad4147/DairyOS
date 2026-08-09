"""Dashboard runtime compatibility facade."""

from typing import Any


class DashboardRuntime:
    """Maintains the cached legacy dashboard projection."""

    def __init__(self, container: Any):
        self.container = container
        self.cached_data = {}

    def rebuild(self):
        self.cached_data = (
            self.container.dashboard_projection_service
            .project_compatibility_dashboard_from_container(
                self.container
            )
        )

        return self.cached_data