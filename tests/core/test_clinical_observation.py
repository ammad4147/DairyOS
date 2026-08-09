from dairyos.herd.health.services.clinical_observation_service import (
    ClinicalObservationService
)



def test_observation_animal_id():

    result = ClinicalObservationService().record(

        "HF-1001",

        "MILK_CHANGE",

        "Reduced production",

        "MEDIUM",

        "Veterinarian"

    )

    assert result.animal_id == "HF-1001"



def test_observation_type():

    result = ClinicalObservationService().record(

        "HF-1001",

        "TEMPERATURE",

        "39.5C",

        "HIGH",

        "Veterinarian"

    )

    assert result.observation_type == "TEMPERATURE"



def test_observation_severity():

    result = ClinicalObservationService().record(

        "HF-1001",

        "APPETITE",

        "Reduced intake",

        "HIGH",

        "Veterinarian"

    )

    assert result.severity == "HIGH"



def test_observer():

    result = ClinicalObservationService().record(

        "HF-1001",

        "BEHAVIOUR",

        "Lethargy",

        "MEDIUM",

        "Dr Ahmed"

    )

    assert result.observed_by == "Dr Ahmed"



def test_observation_timestamp_created():

    result = ClinicalObservationService().record(

        "HF-1001",

        "GENERAL",

        "Normal",

        "LOW",

        "Farm Manager"

    )

    assert result.observed_at is not None



def test_notes_supported():

    result = ClinicalObservationService().record(

        "HF-1001",

        "BODY",

        "Swelling",

        "HIGH",

        "Veterinarian",

        "Check udder condition"

    )

    assert result.notes == "Check udder condition"
