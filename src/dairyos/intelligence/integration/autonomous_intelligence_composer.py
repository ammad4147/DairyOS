"""
DairyOS Autonomous Intelligence Composer

Enterprise composition boundary for autonomous intelligence execution.

Creates:

Prediction
Decision
Governance
Command
Execution
Memory
Learning
Audit

and composes them into:

AutonomousDecisionLoop
"""


from dairyos.intelligence.integration.autonomous_decision_loop import (
    AutonomousDecisionLoop,
)


class AutonomousIntelligenceComposer:
    """
    Creates a fully configured autonomous intelligence loop.
    """


    def __init__(self):

        from dairyos.intelligence.prediction.gateway.prediction_gateway import (
            PredictionGateway,
        )

        from dairyos.intelligence.decision.gateway.decision_gateway import (
            DecisionGateway,
        )

        from dairyos.intelligence.command.gateway.command_gateway import (
            CommandGateway,
        )

        from dairyos.intelligence.execution.gateway.execution_gateway import (
            ExecutionGateway,
        )

        from dairyos.intelligence.memory.gateway.memory_gateway import (
            MemoryGateway,
        )

        from dairyos.intelligence.learning.gateway.learning_gateway import (
            LearningGateway,
        )

        from dairyos.intelligence.integration.decision_governance_service import (
            DecisionGovernanceService,
        )


        self.loop = AutonomousDecisionLoop(
            prediction=PredictionGateway(),
            decision=DecisionGateway(),
            command=CommandGateway(),
            execution=ExecutionGateway(),
            memory=MemoryGateway(),
            learning=LearningGateway(),
            governance=DecisionGovernanceService(),
        )


        from dairyos.intelligence.integration.autonomous_audit_bridge import (
            AutonomousAuditBridge,
        )


        self.audit = AutonomousAuditBridge()



    def get_loop(
        self,
    ):

        return self.loop



    def validate_result(
        self,
        result,
    ):

        from dairyos.intelligence.integration.runtime_contract import (
            AutonomousRuntimeContract,
        )


        contract = AutonomousRuntimeContract()


        return {
            "valid": contract.validate(
                result
            ),
            "missing_fields": contract.missing_fields(
                result
            ),
        }



    def run(
        self,
        context=None,
    ):

        result = self.loop.run(
            context
        )


        if result:

            result["runtime_validation"] = (
                self.validate_result(
                    result
                )
            )


            if result.get(
                "runtime_validation"
            ).get(
                "valid"
            ):

                result["audit"] = (
                    self.audit.record_cycle(
                        result
                    )
                )


        return result
