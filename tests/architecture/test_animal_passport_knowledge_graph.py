from dairyos.platform.knowledge_graph.services.animal_passport_graph_service import AnimalPassportGraphService


def test_animal_passport_graph_is_rebuildable_and_non_authoritative():
    graph = AnimalPassportGraphService().build(
        "A-001",
        {
            "parents": [
                {"relation": "dam", "animal_id": "A-0001"},
                {"relation": "sire", "animal_id": "B-0001"},
            ],
            "descendants": [{"animal_id": "A-001-01"}],
        },
        {
            "milk": [{"id": 11}],
            "health": [{"case_id": "HC-1"}],
            "breeding": [],
            "treatments": [{"id": 4}],
            "feed": [],
            "finance": [{"id": 7}],
            "operational_events": [{"id": 8}],
        },
    )

    assert graph["authoritative"] is False
    assert graph["rebuildable"] is True
    assert graph["node_count"] >= 7
    relations = {item["relation_type"] for item in graph["relationships"]}
    assert {"HAS_DAM", "HAS_SIRE", "HAS_OFFSPRING", "HAS_MILK_RECORD", "HAS_HEALTH_RECORD", "HAS_TREATMENT", "HAS_FINANCE_RECORD", "HAS_OPERATIONAL_EVENT"} <= relations
