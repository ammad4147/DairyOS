from datetime import date
import uuid


def _register_milking_animal(client):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "breed": "Sahiwal",
            "sex": "FEMALE",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": "THRICE_DAILY",
            "ear_tag": f"M20-{uuid.uuid4().hex[:10].upper()}",
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["animal_id"]
    assert body["system_generated_animal_id"] is True

    return body["animal_id"]


def _record_morning_production(client, animal_id, litres):
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "production_date": date.today().isoformat(),
            "milking_session": "MORNING",
            "morning_yield": litres,
            "operator": "M20-REGRESSION",
        },
    )

    assert response.status_code == 200, response.text


def _display_band(row):
    return int(float(row["total_litres"]) + 0.5)


def _assert_disjoint(extremes):
    highest = extremes["highest"]
    lowest = extremes["lowest"]

    highest_ids = {row["animal_id"] for row in highest}
    lowest_ids = {row["animal_id"] for row in lowest}

    highest_bands = {_display_band(row) for row in highest}
    lowest_bands = {_display_band(row) for row in lowest}

    # An animal cannot be simultaneously Highest and Lowest.
    assert highest_ids.isdisjoint(lowest_ids)

    # A displayed production value cannot be present on both sides.
    assert highest_bands.isdisjoint(lowest_bands)


def test_production_extremes_use_disjoint_ranked_bands(client):
    yields = [30.0, 20.0, 15.0, 10.0, 5.0]

    animals = []

    for litres in yields:
        animal_id = _register_milking_animal(client)
        _record_morning_production(client, animal_id, litres)
        animals.append((animal_id, litres))

    response = client.get("/dashboard")

    assert response.status_code == 200, response.text

    extremes = response.json()["milk"]["production_extremes"]

    assert extremes["data_status"] == "LIVE_PERSISTED_DATA"
    assert extremes["population_count"] == 5

    highest = extremes["highest"]
    lowest = extremes["lowest"]

    assert [
        float(row["total_litres"])
        for row in highest
    ] == [30.0, 20.0]

    assert [
        float(row["total_litres"])
        for row in lowest
    ] == [5.0, 10.0]

    # 15 L is the central production band and must be neutral.
    represented_ids = {
        row["animal_id"]
        for row in highest + lowest
    }

    neutral_id = next(
        animal_id
        for animal_id, litres in animals
        if litres == 15.0
    )

    assert neutral_id not in represented_ids

    _assert_disjoint(extremes)


def test_same_displayed_litre_band_never_crosses_both_lists(client):
    # 14.6 L and 15.4 L both display as 15 L in the Dashboard.
    # That visible 15 L band must never appear on both sides.
    yields = [30.0, 20.0, 15.4, 14.6, 10.0, 5.0]

    for litres in yields:
        animal_id = _register_milking_animal(client)
        _record_morning_production(client, animal_id, litres)

    response = client.get("/dashboard")

    assert response.status_code == 200, response.text

    extremes = response.json()["milk"]["production_extremes"]

    _assert_disjoint(extremes)

    highest_bands = {
        _display_band(row)
        for row in extremes["highest"]
    }

    lowest_bands = {
        _display_band(row)
        for row in extremes["lowest"]
    }

    # 15 L is the middle displayed band and therefore neutral.
    assert 15 not in highest_bands
    assert 15 not in lowest_bands


def test_even_number_of_production_bands_split_cleanly(client):
    yields = [30.0, 20.0, 15.0, 10.0]

    for litres in yields:
        animal_id = _register_milking_animal(client)
        _record_morning_production(client, animal_id, litres)

    response = client.get("/dashboard")

    assert response.status_code == 200, response.text

    extremes = response.json()["milk"]["production_extremes"]

    assert [
        _display_band(row)
        for row in extremes["highest"]
    ] == [30, 20]

    assert [
        _display_band(row)
        for row in extremes["lowest"]
    ] == [10, 15]

    _assert_disjoint(extremes)


def test_one_production_band_has_no_meaningful_extremes(client):
    # These all display as the same 15 L production band.
    yields = [15.0, 15.2, 14.8]

    for litres in yields:
        animal_id = _register_milking_animal(client)
        _record_morning_production(client, animal_id, litres)

    response = client.get("/dashboard")

    assert response.status_code == 200, response.text

    extremes = response.json()["milk"]["production_extremes"]

    assert extremes["population_count"] == 3
    assert extremes["data_status"] == "LIVE_PERSISTED_DATA"

    assert extremes["highest"] == []
    assert extremes["lowest"] == []


def test_production_extremes_empty_state_is_collection(client):
    response = client.get("/dashboard")

    assert response.status_code == 200, response.text

    extremes = response.json()["milk"]["production_extremes"]

    assert extremes["highest"] == []
    assert extremes["lowest"] == []
    assert extremes["population_count"] == 0
    assert extremes["data_status"] == "NO_DATA"
