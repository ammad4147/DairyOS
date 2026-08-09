from dairyos.operations.workforce_intelligence.models.workforce_command_snapshot import (
    WorkforceCommandSnapshot,
)



class WorkforceCommandService:
    """
    Consolidates workforce intelligence domains
    into a command-level operational snapshot.
    """



    def __init__(
        self,
        execution_service,
        performance_service,
        reliability_service,
        accountability_service,
        ownership_service,
    ):

        self.execution_service = (
            execution_service
        )

        self.performance_service = (
            performance_service
        )

        self.reliability_service = (
            reliability_service
        )

        self.accountability_service = (
            accountability_service
        )

        self.ownership_service = (
            ownership_service
        )



    def generate_snapshot(
        self,
    ):

        execution = (
            self.execution_service.generate_snapshot()
        )


        performance = (
            self.performance_service.generate_summary()
        )


        reliability = (
            self.reliability_service.generate_summary()
        )


        accountability = (
            self.accountability_service.generate_summary()
        )


        ownership = (
            self.ownership_service.generate_summary()
        )



        attention_required = any(
            [
                execution.attention_required,

                performance.attention_required,

                reliability.attention_required,

                accountability.escalation_required,

                ownership.escalation_required,
            ]
        )



        if attention_required:

            priority_level = "HIGH"

            recommended_action = (
                "Review workforce operational gaps"
            )


        else:

            priority_level = "NORMAL"

            recommended_action = (
                "Maintain workforce operational performance"
            )



        return WorkforceCommandSnapshot(

            execution_health=(
                execution.execution_health
            ),

            performance_status=(
                performance.performance_status
            ),

            reliability_status=(
                reliability.reliability_status
            ),

            accountability_status=(
                accountability.accountability_status
            ),

            ownership_status=(
                ownership.ownership_status
            ),


            execution_score=(
                execution.completion_rate
            ),

            performance_score=(
                performance.reliability_score
            ),

            reliability_score=(
                reliability.reliability_score
            ),

            accountability_score=(
                accountability.accountability_score
            ),

            ownership_score=(
                ownership.ownership_score
            ),


            management_attention_required=(
                attention_required
            ),

            priority_level=(
                priority_level
            ),

            recommended_action=(
                recommended_action
            ),

        )
