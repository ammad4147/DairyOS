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
    assert body["pregnancy_checks"] == 2
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

    factory = RepositoryFactory.create()
    try:
        record = factory.breeding().get_all()[-1]
        record.timestamp = None
        factory.session.commit()
    finally:
        factory.close()

    body = client.get("/farm/reproduction/overview").json()
    assert body["record_count"] == 0
    assert body["data_status"] == "NO_DATA"
