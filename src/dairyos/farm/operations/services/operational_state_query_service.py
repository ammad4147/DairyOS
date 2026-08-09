from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.services.operational_state_read_model import (
    OperationalStateReadModel,
)

from dairyos.farm.operations.alerts.operational_heads_up_service import (
    OperationalHeadsUpService,
)

from dairyos.farm.operations.readiness.operational_readiness_evaluator import (
    OperationalReadinessEvaluator,
)

from dairyos.farm.operations.services.task_lifecycle_intelligence_service import (
    TaskLifecycleIntelligenceService,
)

from dairyos.farm.operations.services.operational_execution_tracking_service import (
    OperationalExecutionTrackingService,
)

from dairyos.farm.operations.services.milk_production_intelligence_service import (
    MilkProductionIntelligenceService,
)

from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)

from dairyos.farm.operations.services.daily_milk_production_command_view_service import (
    DailyMilkProductionCommandViewService,
)


class OperationalStateQueryService:
    """
    Read boundary for current farm operational state.

    Converts domain operational state
    into dashboard-safe read models.

    Does not modify state.
    """


    def __init__(
        self,
        operational_state_service: FarmOperationalStateService,

        heads_up_service:
            OperationalHeadsUpService | None = None,

        readiness_evaluator:
            OperationalReadinessEvaluator | None = None,

        task_lifecycle_intelligence:
            TaskLifecycleIntelligenceService | None = None,

        operational_execution_tracking:
            OperationalExecutionTrackingService | None = None,

        milk_production_intelligence_service:
            MilkProductionIntelligenceService | None = None,

        milk_production_trend_intelligence_service:
            MilkProductionTrendIntelligenceService | None = None,

        daily_milk_production_command_view_service:
            DailyMilkProductionCommandViewService | None = None,

        operations_timeline_service=None,
    ):

        self.operational_state_service = (
            operational_state_service
        )


        self.heads_up_service = (
            heads_up_service
            if heads_up_service is not None
            else OperationalHeadsUpService()
        )


        self.readiness_evaluator = (
            readiness_evaluator
            if readiness_evaluator is not None
            else OperationalReadinessEvaluator(
                operational_state_service
            )
        )


        self.task_lifecycle_intelligence = (
            task_lifecycle_intelligence
            if task_lifecycle_intelligence is not None
            else TaskLifecycleIntelligenceService(
                operational_state_service
            )
        )


        self.operational_execution_tracking = (
            operational_execution_tracking
        )


        if (
            self.operational_execution_tracking is None
            and operations_timeline_service is not None
        ):

            self.operational_execution_tracking = (
                OperationalExecutionTrackingService(
                    operational_state_service,
                    operations_timeline_service,
                )
            )


        self.milk_production_intelligence_service = (
            milk_production_intelligence_service
            if milk_production_intelligence_service is not None
            else MilkProductionIntelligenceService(
                operational_state_service
            )
        )


        self.milk_production_trend_intelligence_service = (
            milk_production_trend_intelligence_service
            if milk_production_trend_intelligence_service is not None
            else MilkProductionTrendIntelligenceService(
                self.milk_production_intelligence_service
            )
        )


        self.daily_milk_production_command_view_service = (
            daily_milk_production_command_view_service
            if daily_milk_production_command_view_service is not None
            else DailyMilkProductionCommandViewService(
                self.milk_production_intelligence_service,
                self.milk_production_trend_intelligence_service,
            )
        )



    def get_current_state(
        self,
    ) -> OperationalStateReadModel:


        state = (
            self.operational_state_service
            .get_state()
        )


        readiness = (
            self.readiness_evaluator
            .evaluate()
        )


        task_intelligence = (
            self.task_lifecycle_intelligence
            .summary()
        )


        milk_intelligence = (
            self.milk_production_intelligence_service
            .summary()
        )


        milk_trend_intelligence = (
            self.milk_production_trend_intelligence_service
            .generate()
            .summary()
        )


        daily_milk_command_view = (
            self.daily_milk_production_command_view_service
            .summary()
        )


        execution_summary = {

            "total_activities": 0,

            "activities": [],

        }


        if self.operational_execution_tracking is not None:

            execution_summary = (
                self.operational_execution_tracking
                .summary()
            )



        completed_execution_count = len(

            [
                activity

                for activity in execution_summary.get(
                    "activities",
                    [],
                )

                if activity.get("status")
                ==
                "COMPLETED_ON_TIME"

            ]

        )



        missed_execution_count = len(

            [
                activity

                for activity in execution_summary.get(
                    "activities",
                    [],
                )

                if activity.get("status")
                ==
                "MISSED"

            ]

        )



        execution_status = "UNKNOWN"


        if execution_summary.get(
            "total_activities",
            0,
        ) > 0:

            execution_status = (

                "COMPLIANT"

                if missed_execution_count == 0

                else

                "ATTENTION_REQUIRED"

            )



        return OperationalStateReadModel(

            farm_id=state.farm_id,

            operational_date=state.operational_date,

            milk_status=dict(
                state.milk_status
            ),

            feeding_status=dict(
                state.feeding_status
            ),

            health_alert_count=len(
                state.health_alerts
            ),

            open_task_count=len(
                state.open_tasks
            ),

            completed_task_count=len(
                state.completed_tasks
            ),

            heads_up_count=state.heads_up_count(),

            heads_up_notifications=list(
                state.heads_up_notifications
            ),

            exception_count=len(
                state.exceptions
            ),

            milk_total=state.milk_total(),

            feed_total=state.feed_total(),

            health_status=state.health_status(),

            operational_status=state.operational_status(),


            readiness_status=readiness[
                "overall_status"
            ],

            readiness_risks=readiness[
                "risks"
            ],


            milk_production_intelligence=milk_intelligence,


            milk_production_analytics=milk_intelligence.get(
                "production_analytics",
                {},
            ),


            milk_production_trend_intelligence=
                milk_trend_intelligence,


            daily_milk_production_command_view=
                daily_milk_command_view,


            open_tasks=list(
                state.open_tasks
            ),


            completed_tasks=list(
                state.completed_tasks
            ),


            task_intelligence=task_intelligence,


            execution_total_activities=execution_summary.get(
                "total_activities",
                0,
            ),


            execution_completed_activities=
                completed_execution_count,


            execution_missed_activities=
                missed_execution_count,


            execution_status=execution_status,


            execution_details=execution_summary.get(
                "activities",
                [],
            ),

        )



    def summary(
        self,
    ):

        return self.get_current_state()



    def get_health_alerts(
        self,
    ):

        state = (
            self.operational_state_service
            .get_state()
        )

        return list(
            state.health_alerts
        )



    def get_exceptions(
        self,
    ):

        state = (
            self.operational_state_service
            .get_state()
        )

        return list(
            state.exceptions
        )
