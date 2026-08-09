from dairyos.milk.integration import (
    MilkHealthBridgeService,
)

from dairyos.herd.health.services.health_risk_assessment_service import (
    HealthRiskAssessmentService,
)



def test_milk_drop_creates_health_signal():


    anomaly = {

        "animal_id": "HF-021",

        "anomaly": "MILK_DROP",

        "deviation_percentage": 45,

        "severity": "HIGH",

    }


    signal = MilkHealthBridgeService().create_signal(
        anomaly
    )


    assert signal.signal_type == "MILK_YIELD_DROP"

    assert signal.severity == "HIGH"



def test_milk_drop_health_assessment():


    anomaly = {

        "animal_id": "HF-021",

        "severity": "HIGH",

    }


    assessment = MilkHealthBridgeService().assess_milk_event(

        "HF-021",

        anomaly,

        HealthRiskAssessmentService()

    )


    assert assessment.risk_level == "HIGH"

    assert (
        "Veterinary examination"
        in assessment.recommended_checks
    )
