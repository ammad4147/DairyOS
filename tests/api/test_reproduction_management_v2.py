from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.repositories.repository_factory import RepositoryFactory


def test_reproduction_overview_counts_one_conception_for_multiple_positive_checks(client, registered_animal):
    for event_type, result in (
        ("insemination", "completed"),
        ("pregnancy_diagnosis", "pregnant"),
        ("pregnancy_confirmed", "confirmed"),
    ):
        response = client.post(
            "/farm/breeding",
            json={
                "animal_id": registered_animal,
                "event_type": event_type,
                "technician": "Dr Vet",
                "result": result,
                "operator": "Dr Vet",
            },
        )
        assert response.status_code == 200, response.text

    body = client.get("/farm/reproduction/overview").json()
    assert body["inseminations"] == 1
    # pregnancy_confirmed is outcome evidence, not a second pregnancy-check
    # encounter. It is intentionally excluded from this encounter count.
    assert body["pregnancy_checks"] == 1
    assert body["services_with_documented_outcome"] == 1
    assert body["confirmed_pregnancies"] == 1
    assert body["conception_rate_percent"] == 100.0


def test_reproduction_overview_excludes_records_without_timestamp_from_current_window(client, registered_animal):
    response = client.post(
        "/farm/breeding",
        json={
            "animal_id": registered_animal,
            "event_type": "heat_detection",
            "technician": "Dr Vet",
            "result": "detected",
            "operator": "Dr Vet",
        },
    )
    assert response.status_code == 200, response.text

    # The domain repository returns detached dataclass records. Mutating one
    # of those objects does not update PostgreSQL, so this test must mutate
    # the persisted row itself to exercise the API's null-timestamp boundary.
    factory = RepositoryFactory.create()
    try:
        row = (
            factory.session.query(BreedingRecordModel)
            .filter(
                BreedingRecordModel.animal_id == registered_animal,
                BreedingRecordModel.event_type == "heat_detection",
                BreedingRecordModel.result == "detected",
            )
            .order_by(BreedingRecordModel.record_id.desc())
            .first()
        )
        assert row is not None
        row.timestamp = None
        factory.session.commit()
    finally:
        factory.close()

    body = client.get("/farm/reproduction/overview").json()
    assert body["record_count"] == 0
    assert body["data_status"] == "NO_DATA"
