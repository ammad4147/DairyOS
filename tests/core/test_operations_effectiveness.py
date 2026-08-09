from datetime import datetime


from dairyos.operations.effectiveness.models.operational_effectiveness import (
    OperationalEffectiveness,
)

from dairyos.operations.effectiveness.services.effectiveness_calculation_service import (
    EffectivenessCalculationService,
)

from dairyos.operations.effectiveness.services.effectiveness_analysis_service import (
    EffectivenessAnalysisService,
)



def test_effectiveness_calculation():

    service = EffectivenessCalculationService()


    score = service.calculate(
        90,
        80,
        70,
    )


    assert score == 80



def test_effectiveness_analysis():

    effectiveness = OperationalEffectiveness(
        effectiveness_id="EFF-001",
        operation_reference="CLS-001",
        response_score=90,
        resolution_score=85,
        closure_score=95,
        created_at=datetime.now(),
    )


    service = EffectivenessAnalysisService()


    result = service.evaluate(effectiveness)


    assert result == "EFFECTIVE"
