"""
DairyOS Intelligence Dashboard Bridge

Enterprise presentation boundary.

Connects autonomous intelligence
with dashboard consumption.

Responsibilities:

- transform runtime intelligence result
- expose dashboard summary
- avoid coupling dashboard models
  with intelligence execution
"""


class IntelligenceDashboardBridge:
    """
    Converts intelligence runtime output
    into dashboard consumable structure.
    """


    def build_summary(
        self,
        result: dict,
    ):

        runtime = result.get(
            "runtime",
            {},
        )


        governance = result.get(
            "governance",
        )


        return {
            "component": "intelligence_dashboard",
            "status": runtime.get(
                "status",
                "unknown",
            ),
            "cycle_id": runtime.get(
                "cycle_id",
            ),
            "stage_count": runtime.get(
                "stage_count",
                0,
            ),
            "stages": runtime.get(
                "stages",
                [],
            ),
            "governance": (
                {
                    "status": governance.status,
                    "approved": governance.approved,
                    "reason": governance.reason,
                }
                if governance
                else None
            ),
            "runtime_validation": result.get(
                "runtime_validation",
            ),
        }