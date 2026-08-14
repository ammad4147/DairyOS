from datetime import datetime

from dairyos.core.time_utils import utcnow

from dairyos.herd.health.services.health_risk_assessment_service import (
    HealthRiskAssessmentService
)

from dairyos.herd.health.models.health_signal import HealthSignal

from dairyos.herd.health.models.clinical_observation import (
    ClinicalObservation
)



def test_high_health_risk_detection():

    signal = HealthSignal(

        "HF-5001",

        "MILK_YIELD_DROP",

        "20",

        "30",

        "33%",

        "HIGH",

        "Milking System",

        utcnow()

    )


    result = HealthRiskAssessmentService().assess(

        "HF-5001",

        [signal]

    )


    assert result.risk_level == "HIGH"



def test_recommended_checks_created():

    signal = HealthSignal(

        "HF-5002",

        "MILK_YIELD_DROP",

        "20",

        "30",

        "33%",

        "HIGH",

        "Milking System",

        utcnow()

    )


    result = HealthRiskAssessmentService().assess(

        "HF-5002",

        [signal]

    )


    assert len(result.recommended_checks) > 0



def test_clinical_observation_increases_risk():

    observation = ClinicalObservation(

        "HF-5003",

        "UDDER",

        "Swelling",

        "HIGH",

        "Veterinarian",

        utcnow(),

        "Possible mastitis"

    )


    result = HealthRiskAssessmentService().assess(

        "HF-5003",

        [],

        [observation]

    )


    assert result.risk_level == "HIGH"



def test_health_alert_creation():

    signal = HealthSignal(

        "HF-5004",

        "FEED_INTAKE_DROP",

        "18",

        "24",

        "25%",

        "HIGH",

        "Feed System",

        utcnow()

    )


    assessment = HealthRiskAssessmentService().assess(

        "HF-5004",

        [signal]

    )


    alert = HealthRiskAssessmentService().create_alert(

        assessment

    )


    assert alert.status == "OPEN"

    assert alert.severity == "HIGH"
