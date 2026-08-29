from __future__ import annotations

from dairyos.platform.knowledge_graph.services.relationship_service import RelationshipService


class AnimalPassportGraphService:
    """Build a transient relationship graph from authoritative Passport facts.

    The graph is intentionally non-persistent: PostgreSQL/domain records remain
    authoritative and the graph can always be rebuilt from the Passport.
    """

    DOMAIN_RELATIONS = (
        ("milk", "HAS_MILK_RECORD"),
        ("health", "HAS_HEALTH_RECORD"),
        ("breeding", "HAS_BREEDING_RECORD"),
        ("treatments", "HAS_TREATMENT"),
        ("feed", "HAS_FEED_RECORD"),
        ("finance", "HAS_FINANCE_RECORD"),
        ("operational_events", "HAS_OPERATIONAL_EVENT"),
    )

    def __init__(self, relationship_service: RelationshipService | None = None):
        self.relationship_service = relationship_service or RelationshipService()

    def build(self, animal_id: str, lineage: dict, history: dict) -> dict:
        nodes: dict[str, dict] = {animal_id: {"id": animal_id, "type": "ANIMAL"}}
        relationships = []

        def connect(source_id: str, relation_type: str, target_id: str, target_type: str):
            nodes.setdefault(target_id, {"id": target_id, "type": target_type})
            relation = self.relationship_service.connect(source_id, relation_type, target_id)
            relationships.append({
                "source_id": relation.source_id,
                "relation_type": relation.relation_type,
                "target_id": relation.target_id,
            })

        for parent in lineage.get("parents", []):
            parent_id = parent.get("animal_id")
            if parent_id:
                relation = "HAS_DAM" if parent.get("relation") == "dam" else "HAS_SIRE"
                connect(animal_id, relation, str(parent_id), "ANIMAL")

        for descendant in lineage.get("descendants", []):
            child_id = descendant.get("animal_id")
            if child_id:
                connect(animal_id, "HAS_OFFSPRING", str(child_id), "ANIMAL")

        for domain, relation_type in self.DOMAIN_RELATIONS:
            for index, record in enumerate(history.get(domain, [])):
                record_id = record.get("id") or record.get("case_id") or record.get("animal_id") or f"{domain}:{animal_id}:{index}"
                target_id = f"{domain}:{record_id}"
                connect(animal_id, relation_type, target_id, domain.upper())

        return {
            "authoritative": False,
            "rebuildable": True,
            "source": "Animal Passport persisted domain projections",
            "node_count": len(nodes),
            "relationship_count": len(relationships),
            "nodes": list(nodes.values()),
            "relationships": relationships,
        }
