"""Input-driven multi-generation Animal Passport simulation."""


def _register(client, *, tag, lifecycle, dam_id=None, sex="FEMALE"):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "ear_tag": tag,
            "breed": "HF",
            "sex": sex,
            "lifecycle_status": lifecycle,
            "dam_id": dam_id,
        },
    )
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
    milking = _register(client, tag="SIM-MILKING-001", lifecycle="LACTATING", dam_id=mother)

    grandchild = _register(
        client,
        tag="SIM-GRANDCALF-001",
        lifecycle="CALF",
        dam_id=heifer,
    )

    mother_passport = _passport(client, mother)
    descendants = mother_passport["lineage"]["descendants"]
    descendant_ids = {row["animal_id"] for row in descendants}
    assert {calf, heifer, milking, grandchild}.issubset(descendant_ids)

    direct_children = [
        row for row in descendants
        if row["depth"] == 1 and row["animal_id"] in {calf, heifer, milking}
    ]
    assert {row["animal_id"] for row in direct_children} == {calf, heifer, milking}
    assert {row["lifecycle_status"] for row in direct_children} == {"CALF", "HEIFER", "LACTATING"}

    heifer_passport = _passport(client, heifer)
    assert heifer_passport["animal"]["dam_id"] == mother
    assert any(row["animal_id"] == grandchild for row in heifer_passport["lineage"]["descendants"])

    for child_id, expected_lifecycle in (
        (calf, "CALF"),
        (heifer, "HEIFER"),
        (milking, "LACTATING"),
    ):
        child_passport = _passport(client, child_id)
        assert child_passport["animal"]["dam_id"] == mother
        assert child_passport["animal"]["lifecycle_status"] == expected_lifecycle
        assert any(
            parent["relation"] == "dam" and parent["animal_id"] == mother
            for parent in child_passport["lineage"]["parents"]
        )


def test_lineage_passport_ui_exposes_clickable_animal_id_navigation():
    from pathlib import Path

    source = Path("src/DairyOS.Web/src/components/AnimalPassportModal.tsx").read_text(encoding="utf-8")
    assert "onOpenPassport" in source
    assert "Offspring / Descendants — click Animal ID to open its Passport" in source
    assert "onClick={()=>onOpen?.(id)}" in source
