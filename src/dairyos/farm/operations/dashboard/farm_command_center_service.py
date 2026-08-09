from dairyos.farm.operations.dashboard.farm_command_center import (
    FarmCommandCenter,
)


class FarmCommandCenterService:
    """
    Builds the Farm Command Center projection.

    Projection chain:

        Farm Operational State
                ↓
        Intelligence Projection
                ↓
        Farm Command Center
                ↓
        API / Dashboard


    Responsibilities:
        - read operational projections
        - assemble management view
        - expose intelligence signals

    Does not:
        - mutate operational state
        - create operational records
        - execute farm activities
    """


    def __init__(
        self,
        dashboard_service=None,
        operational_state_query_service=None,
        execution_compliance_service=None,
        operations_runtime=None,
    ):

        self.dashboard_service = (
            dashboard_service
        )

        self.operational_state_query_service = (
            operational_state_query_service
        )

        self.execution_compliance_service = (
            execution_compliance_service
        )

        self.operations_runtime = (
            operations_runtime
        )



    def _normalize(
        self,
        value,
    ):

        if isinstance(
            value,
            dict,
        ):
            return value


        if hasattr(
            value,
            "__dict__",
        ):
            return value.__dict__


        return {}



    def _read_dashboard(
        self,
    ):

        if self.dashboard_service is None:
            return {}


        if hasattr(
            self.dashboard_service,
            "build_dashboard",
        ):

            return self._normalize(
                self.dashboard_service
                .build_dashboard()
            )


        if hasattr(
            self.dashboard_service,
            "build",
        ):

            return self._normalize(
                self.dashboard_service
                .build()
            )


        return self._normalize(
            self.dashboard_service
        )



    def _read_operational_state(
        self,
    ):

        if (
            self.operational_state_query_service
            is None
        ):
            return {}


        if hasattr(
            self.operational_state_query_service,
            "get_current_state",
        ):

            return self._normalize(
                self.operational_state_query_service
                .get_current_state()
            )


        if hasattr(
            self.operational_state_query_service,
            "get_state",
        ):

            return self._normalize(
                self.operational_state_query_service
                .get_state()
            )


        return {}



    def _read_execution_compliance(
        self,
    ):

        if (
            self.execution_compliance_service
            is None
        ):
            return {}


        if hasattr(
            self.execution_compliance_service,
            "summary",
        ):

            return self._normalize(
                self.execution_compliance_service
                .summary()
            )


        if hasattr(
            self.execution_compliance_service,
            "evaluate",
        ):

            return self._normalize(
                self.execution_compliance_service
                .evaluate()
            )


        if hasattr(
            self.execution_compliance_service,
            "build",
        ):

            return self._normalize(
                self.execution_compliance_service
                .build()
            )


        return {}



    def build(
        self,
    ):

        dashboard = (
            self._read_dashboard()
        )

        operational_state = (
            self._read_operational_state()
        )

        compliance = (
            self._read_execution_compliance()
        )


        projection = {}

        projection.update(
            operational_state
        )

        projection.update(
            dashboard
        )


        expected = compliance.get(
            "expected_activities",
            compliance.get(
                "scheduled_activities",
                0,
            ),
        )


        missed = compliance.get(
            "missed_activities",
            compliance.get(
                "overdue_activities",
                0,
            ),
        )


        return FarmCommandCenter(

            milk_today=projection.get(
                "milk_today",
                0,
            ),


            feed_quantity_today=projection.get(
                "feed_quantity_today",
                0,
            ),


            feed_cost_today=projection.get(
                "feed_cost_today",
                0,
            ),


            health_alerts=projection.get(
                "health_alerts",
                0,
            ),


            breeding_pending=projection.get(
                "breeding_pending",
                0,
            ),


            operational_status=projection.get(
                "operational_status",
                "normal",
            ),


            attention_items=projection.get(
                "attention_items",
                [],
            ),


            milk_anomalies=projection.get(
                "milk_anomalies",
                0,
            ),


            milk_health_risks=projection.get(
                "milk_health_risks",
                0,
            ),


            milk_recommended_checks=projection.get(
                "milk_recommended_checks",
                [],
            ),


            open_tasks=projection.get(
                "open_tasks",
                [],
            ),


            completed_tasks=projection.get(
                "completed_tasks",
                [],
            ),


            heads_up_notifications=projection.get(
                "heads_up_notifications",
                [],
            ),


            decisions=projection.get(
                "decisions",
                [],
            ),


            execution_total_activities=projection.get(
                "execution_total_activities",
                expected,
            ),


            execution_completed_activities=projection.get(
                "execution_completed_activities",
                max(
                    expected - missed,
                    0,
                ),
            ),


            execution_missed_activities=projection.get(
                "execution_missed_activities",
                missed,
            ),


            execution_status=projection.get(
                "execution_status",
                compliance.get(
                    "compliance_status",
                    "UNKNOWN",
                ),
            ),


            execution_details=projection.get(
                "execution_details",
                compliance.get(
                    "missed_items",
                    [],
                ),
            ),


            execution_history_compliance=compliance,


            execution_compliance_rate=(
                (
                    expected - missed
                )
                /
                expected
                if expected
                else 0.0
            ),


            execution_scheduled_activities=expected,


            execution_overdue_activities=missed,


            execution_risk_level=(
                "HIGH"
                if missed > 0
                else "LOW"
            ),


            execution_attention_required=(
                missed > 0
            ),
        )
