"""Input-driven multi-generation Animal Passport simulation."""


def _register(client, *, tag, lifecycle, dam_id=None, sex="FEMALE", milking_frequency=None):
    payload = {
        "animal_type": "CATTLE",
        "ear_tag": tag,
        "breed": "HF",
        "sex": sex,
        "lifecycle_status": lifecycle,
        "dam_id": dam_id,
    }
    if milking_frequency is not None:
        payload["milking_frequency"] = milking_frequency
    response = client.post("/farm/animals", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def _passport(client, animal_id):
    response = client.get(f"/farm/animals/{animal_id}/passport")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["animal"]["animal_id"] == animal_id, body
    return body


def test_multi_generation_lineage_is_preserved_and_descendants_are_addressable(client):
    mother = _register(client, tag="SIM-MOTHER-001", lifecycle="HEIFER")

    transition = client.patch(
        f"/farm/animals/{mother}/lifecycle",
        json={"lifecycle_status": "LACTATING", "operator": "simulation"},
    )
    assert transition.status_code == 200, transition.text

    calving = client.post(
        "/farm/breeding",
        json={
            "animal_id": mother,
            "event_type": "calving",
            "technician": "simulation",
            "result": "CALVED",
            "operator": "simulation",
        },
    )
    assert calving.status_code == 200, calving.text

    calf = _register(client, tag="SIM-CALF-001", lifecycle="CALF", dam_id=mother)
    heifer = _register(client, tag="SIM-HEIFER-001", lifecycle="HEIFER", dam_id=mother)
    milking = _register(
        client,
        tag="SIM-MILKING-001",
        lifecycle="LACTATING",
        dam_id=mother,
        milking_frequency="TWICE_DAILY",
    )
    cycle_animal = _register(client, tag="SIM-CYCLE-001", lifecycle="CALF", dam_id=mother)
    grandchild = _register(client, tag="SIM-GRANDCALF-001", lifecycle="CALF", dam_id=heifer)

    # Exercise the requested life-cycle progression separately:
    # calf -> heifer -> milking cow -> calf.
    calf_to_heifer = client.patch(
        f"/farm/animals/{cycle_animal}/lifecycle",
        json={"lifecycle_status": "HEIFER", "operator": "simulation"},
    )
    assert calf_to_heifer.status_code == 200, calf_to_heifer.text
    assert _passport(client, cycle_animal)["animal"]["lifecycle_status"] == "HEIFER"

    heifer_to_milking = client.patch(
        f"/farm/animals/{cycle_animal}/lifecycle",
        json={
            "lifecycle_status": "LACTATING",
            "operator": "simulation",
            "production_group": "MILKING",
        },
    )
    assert heifer_to_milking.status_code == 200, heifer_to_milking.text

    frequency_change = client.post(
        f"/farm/animals/{cycle_animal}/milking-frequency",
        json={
            "milking_frequency": "TWICE_DAILY",
            "changed_by": "simulation",
            "reason": "Cycle simulation reached milking cow",
        },
    )
    assert frequency_change.status_code == 200, frequency_change.text

    cycle_passport = _passport(client, cycle_animal)
    assert cycle_passport["animal"]["lifecycle_status"] == "LACTATING"
    assert cycle_passport["animal"]["milking_frequency"] == "TWICE_DAILY"

    cycle_child = _register(client, tag="SIM-CYCLE-CALF-001", lifecycle="CALF", dam_id=cycle_animal)

    mother_passport = _passport(client, mother)
    descendants = mother_passport["lineage"]["descendants"]
    descendant_ids = {row["animal_id"] for row in descendants}
    assert {calf, heifer, milking, cycle_animal, grandchild, cycle_child}.issubset(descendant_ids)

    direct_children = {
        row["animal_id"]: row
        for row in descendants
        if row["depth"] == 1
    }
    assert direct_children[calf]["lifecycle_status"] == "CALF"
    assert direct_children[heifer]["lifecycle_status"] == "HEIFER"
    assert direct_children[milking]["lifecycle_status"] == "LACTATING"
    assert direct_children[milking]["animal_id"] == milking
    assert direct_children[milking]["depth"] == 1

    heifer_passport = _passport(client, heifer)
    assert heifer_passport["animal"]["dam_id"] == mother
    assert any(row["animal_id"] == grandchild for row in heifer_passport["lineage"]["descendants"])

    milking_passport = _passport(client, milking)
    assert milking_passport["animal"]["dam_id"] == mother
    assert milking_passport["animal"]["lifecycle_status"] == "LACTATING"
    assert milking_passport["animal"]["milking_frequency"] == "TWICE_DAILY"

    cycle_passport = _passport(client, cycle_animal)
    assert cycle_passport["animal"]["dam_id"] == mother
    assert any(row["animal_id"] == cycle_child for row in cycle_passport["lineage"]["descendants"])


def test_lineage_passport_ui_exposes_clickable_animal_id_navigation():
    from pathlib import Path

    modal_source = Path("src/DairyOS.Web/src/components/AnimalPassportModal.tsx").read_text(encoding="utf-8")
    app_source = Path("src/DairyOS.Web/src/App.tsx").read_text(encoding="utf-8")
    assert "onOpenPassport" in modal_source
    assert "Offspring / Descendants — click Animal ID to open its Passport" in modal_source
    assert "onClick={()=>onOpen?.(id)}" in modal_source
    assert "onOpenPassport={openLinkedPassport}" in app_source
