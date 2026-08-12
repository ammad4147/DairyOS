def test_lifetime_animal_passport_aggregates_persisted_history(client, registered_animal):
    milk = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "operator": "Milking Operator",
        },
    )
    assert milk.status_code == 200, milk.text

    feed = client.post(
        "/farm/feed",
        json={
            "animal_id": registered_animal,
            "feed_type": "silage",
            "quantity_kg": 12.5,
            "operator": "Feed Operator",
        },
    )
    assert feed.status_code == 200, feed.text

    health = client.post(
        "/farm/health-observations",
        json={
            "animal_id": registered_animal,
            "symptom": "Lethargy",
            "severity": "ELEVATED",
            "operator": "Dr Vet",
        },
    )
    assert health.status_code == 200, health.text

    breeding = client.post(
        "/farm/breeding",
        json={
            "animal_id": registered_animal,
            "event_type": "insemination",
            "technician": "Dr Vet",
            "result": "completed",
            "operator": "Dr Vet",
        },
    )
    assert breeding.status_code == 200, breeding.text

    finance = client.post(
        "/farm/financial",
        json={
            "transaction_type": "EXPENSE",
            "amount": 1250.0,
            "category": "Animal Feed",
            "operator": "Finance Operator",
            "animal_id": registered_animal,
        },
    )
    assert finance.status_code == 200, finance.text

    passport = client.get(f"/farm/animals/{registered_animal}/passport")

    assert passport.status_code == 200, passport.text
    body = passport.json()
    assert body["animal"]["animal_id"] == registered_animal
    assert body["record_counts"]["milk"] >= 1
    assert body["record_counts"]["feed"] >= 1
    assert body["record_counts"]["health"] >= 1
    assert body["record_counts"]["breeding"] >= 1
    assert body["record_counts"]["finance"] >= 1
    assert body["history"]["milk"][0]["animal_id"] == registered_animal
    assert body["history"]["feed"][0]["animal_id"] == registered_animal
    assert body["history"]["health"][0]["animal_id"] == registered_animal
    assert body["history"]["breeding"][0]["animal_id"] == registered_animal
    assert body["history"]["finance"][0]["animal_id"] == registered_animal

    timeline = body["timeline"]
    assert timeline
    assert {item["domain"] for item in timeline} >= {
        "milk",
        "feed",
        "health",
        "breeding",
        "finance",
    }
    timestamps = [str(item["timestamp"]) for item in timeline]
    assert timestamps == sorted(timestamps)


def test_lifetime_animal_passport_requires_existing_permanent_id(client):
    response = client.get("/farm/animals/AN-NOT-REGISTERED/passport")
    assert response.status_code == 404
