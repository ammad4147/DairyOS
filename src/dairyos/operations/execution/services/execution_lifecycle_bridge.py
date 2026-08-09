from dairyos.operations.command_outcome.services.command_outcome_service import (
    CommandOutcomeService,
)

from dairyos.operations.command_verification.services.command_verification_service import (
    CommandVerificationService,
)

from dairyos.operations.closure_intelligence.services.closure_intelligence_service import (
    ClosureIntelligenceService,
)


class ExecutionLifecycleBridge:
    """
    Connects completed execution
    with outcome, verification,
    and closure assessment.

    Flow:

    OperationalExecution
            |
            v
    Outcome
            |
            v
    Verification
            |
            v
    Closure Assessment


    Does not:
    - complete execution
    - verify automatically
    - close operational issues
    """


    def __init__(
        self,
        outcome_service=None,
        verification_service=None,
        closure_service=None,
    ):

        self.outcome_service = (
            outcome_service
            if outcome_service is not None
            else CommandOutcomeService()
        )


        self.verification_service = (
            verification_service
            if verification_service is not None
            else CommandVerificationService()
        )


        self.closure_service = (
            closure_service
            if closure_service is not None
            else ClosureIntelligenceService()
        )


    def _validate_execution(
        self,
        execution,
    ):

        if execution is None:

            raise ValueError(
                "OperationalExecution is required"
            )


        if not execution.execution_id:

            raise ValueError(
                "OperationalExecution requires execution_id"
            )


    def record_execution_outcome(
        self,
        execution,
        impact_score: float,
        notes: str,
    ):

        self._validate_execution(
            execution
        )


        return self.outcome_service.record_outcome(

            outcome_id=(
                f"OUT-{execution.execution_id}"
            ),

            command_id=(
                execution.execution_id
            ),

            impact_score=impact_score,

            notes=notes,

        )


    def verify_execution(
        self,
        execution,
        success: bool,
        message: str,
    ):

        self._validate_execution(
            execution
        )


        return self.verification_service.verify(

            verification_id=(
                f"VER-{execution.execution_id}"
            ),

            execution_id=execution.execution_id,

            success=success,

            message=message,

        )


    def assess_closure(
        self,
        execution,
        task_name: str,
        completed: bool,
        performance_score: float,
    ):

        self._validate_execution(
            execution
        )


        return self.closure_service.assess(

            execution_id=execution.execution_id,

            task_name=task_name,

            completed=completed,

            performance_score=performance_score,

        )
