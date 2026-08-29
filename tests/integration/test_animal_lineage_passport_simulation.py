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
    grandchild = _register(client, tag="SIM-GRANDCALF-001", lifecycle="CALF", dam_id=heifer)

    # Exercise: calf -> heifer -> milking cow -> calf.
    calf_to_heifer = client.patch(
        f"/farm/animals/{calf}/lifecycle",
        json={"lifecycle_status": "HEIFER", "operator": "simulation"},
    )
    assert calf_to_heifer.status_code == 200, calf_to_heifer.text
    assert _passport(client, calf)["animal"]["lifecycle_status"] == "HEIFER"

    heifer_to_milking = client.patch(
        f"/farm/animals/{calf}/lifecycle",
        json={
            "lifecycle_status": "LACTATING",
            "operator": "simulation",
            "production_group": "MILKING",
            "milking_frequency": "TWICE_DAILY",
        },
    )
    assert heifer_to_milking.status_code == 200, heifer_to_milking.text
    calf_after_lactation = _passport(client, calf)
    assert calf_after_lactation["animal"]["lifecycle_status"] == "LACTATING"
    assert calf_after_lactation["animal"]["milking_frequency"] == "TWICE_DAILY"

    new_child = _register(client, tag="SIM-CALF-002", lifecycle="CALF", dam_id=calf)

    mother_passport = _passport(client, mother)
    descendants = mother_passport["lineage"]["descendants"]
    descendant_ids = {row["animal_id"] for row in descendants}
    assert {calf, heifer, milking, grandchild, new_child}.issubset(descendant_ids)

    direct_children = [
        row for row in descendants
        if row["depth"] == 1 and row["animal_id"] in {calf, heifer, milking}
    ]
    assert {row["animal_id"] for row in direct_children} == {calf, heifer, milking}
    assert {row["animal_id"] for row in direct_children} == {calf, heifer, milking}
    direct_lifecycles = {row["animal_id"]: row["lifecycle_status"] for row in direct_children}
    assert direct_lifecycles == {calf: "LACTATING", heifer: "HEIFER", milking: "LACTATING"}

    heifer_passport = _passport(client, heifer)
    assert heifer_passport["animal"]["dam_id"] == mother
    assert any(row["animal_id"] == grandchild for row in heifer_passport["lineage"]["descendants"])

    milking_passport = _passport(client, milking)
    assert milking_passport["animal"]["dam_id"] == mother
    assert milking_passport["animal"]["lifecycle_status"] == "LACTATING"
    assert milking_passport["animal"]["milking_frequency"] == "TWICE_DAILY"

    calf_after_lactation = _passport(client, calf)
    assert calf_after_lactation["animal"]["dam_id"] == mother
    assert any(row["animal_id"] == new_child for row in calf_after_lactation["lineage"]["descendants"])


def test_lineage_passport_ui_exposes_clickable_animal_id_navigation():
    from pathlib import Path

    modal_source = Path("src/DairyOS.Web/src/components/AnimalPassportModal.tsx").read_text(encoding="utf-8")
    app_source = Path("src/DairyOS.Web/src/App.tsx").read_text(encoding="utf-8")
    assert "onOpenPassport" in modal_source
    assert "Offspring / Descendants — click Animal ID to open its Passport" in modal_source
    assert "onClick={()=>onOpen?.(id)}" in modal_source
    assert "onOpenPassport={openLinkedPassport}" in app_source
