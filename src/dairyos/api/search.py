"""
Optional Elasticsearch search projection for DairyOS animals.

PostgreSQL / AnimalRepository remains authoritative.
Elasticsearch is a disposable search projection and is never required for
normal DairyOS operation.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from elasticsearch import Elasticsearch
from fastapi import APIRouter, HTTPException, Query


logger = logging.getLogger(__name__)

ELASTICSEARCH_URL = os.getenv(
    "DAIRYOS_ELASTICSEARCH_URL",
    "http://127.0.0.1:9200",
).strip()

ANIMAL_INDEX = os.getenv(
    "DAIRYOS_ELASTICSEARCH_ANIMAL_INDEX",
    "dairyos-animals",
).strip()

router = APIRouter(
    prefix="/api/search",
    tags=["search"],
)


def create_search_client() -> Elasticsearch:
    return Elasticsearch(
        ELASTICSEARCH_URL,
        request_timeout=2,
    )


def animal_document(animal: Any) -> dict[str, Any]:
    dob = getattr(animal, "date_of_birth", None)

    return {
        "animal_id": str(getattr(animal, "animal_id", "") or ""),
        "legacy_animal_id": str(
            getattr(animal, "legacy_animal_id", "") or ""
        ),
        "ear_tag": str(getattr(animal, "ear_tag", "") or ""),
        "rfid": str(getattr(animal, "rfid", "") or ""),
        "animal_type": str(getattr(animal, "animal_type", "") or ""),
        "breed": str(getattr(animal, "breed", "") or ""),
        "sex": str(getattr(animal, "sex", "") or ""),
        "status": str(getattr(animal, "status", "") or ""),
        "lifecycle_status": str(
            getattr(animal, "lifecycle_status", "") or ""
        ),
        "active": bool(getattr(animal, "active", False)),
        "production_group": str(
            getattr(animal, "production_group", "") or ""
        ),
        "location": str(getattr(animal, "location", "") or ""),
        "date_of_birth": dob.isoformat() if dob else None,
    }


ANIMAL_INDEX_MAPPINGS = {
    "properties": {
        "animal_id": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "legacy_animal_id": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "ear_tag": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "rfid": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "animal_type": {"type": "keyword"},
        "breed": {"type": "text"},
        "sex": {"type": "keyword"},
        "status": {"type": "keyword"},
        "lifecycle_status": {"type": "keyword"},
        "active": {"type": "boolean"},
        "production_group": {"type": "keyword"},
        "location": {"type": "text"},
        "date_of_birth": {"type": "date"},
    }
}


def ensure_animal_index(client: Elasticsearch) -> None:
    if client.indices.exists(index=ANIMAL_INDEX):
        return

    client.indices.create(
        index=ANIMAL_INDEX,
        mappings=ANIMAL_INDEX_MAPPINGS,
    )


def _hits_payload(query: str, response: dict[str, Any]) -> dict[str, Any]:
    hits = response["hits"]

    return {
        "query": query,
        "total": int(hits["total"]["value"]),
        "results": [
            hit["_source"]
            for hit in hits["hits"]
        ],
    }


def _exact_identifier_search(
    client: Elasticsearch,
    term: str,
) -> dict[str, Any]:
    return client.search(
        index=ANIMAL_INDEX,
        size=20,
        query={
            "bool": {
                "should": [
                    {"term": {"animal_id.keyword": term}},
                    {"term": {"legacy_animal_id.keyword": term}},
                    {"term": {"ear_tag.keyword": term}},
                    {"term": {"rfid.keyword": term}},
                ],
                "minimum_should_match": 1,
            }
        },
    )


def _general_search(
    client: Elasticsearch,
    term: str,
) -> dict[str, Any]:
    """
    General search after exact identifiers have failed.

    Identifier fields use prefix matching, not fuzziness.
    Fuzzy matching is reserved for descriptive text.
    """
    return client.search(
        index=ANIMAL_INDEX,
        size=20,
        query={
            "bool": {
                "should": [
                    {
                        "prefix": {
                            "animal_id.keyword": {
                                "value": term,
                                "case_insensitive": True,
                            }
                        }
                    },
                    {
                        "prefix": {
                            "legacy_animal_id.keyword": {
                                "value": term,
                                "case_insensitive": True,
                            }
                        }
                    },
                    {
                        "prefix": {
                            "ear_tag.keyword": {
                                "value": term,
                                "case_insensitive": True,
                            }
                        }
                    },
                    {
                        "prefix": {
                            "rfid.keyword": {
                                "value": term,
                                "case_insensitive": True,
                            }
                        }
                    },
                    {
                        "multi_match": {
                            "query": term,
                            "fields": [
                                "breed^2",
                                "location",
                            ],
                            "fuzziness": "AUTO",
                        }
                    },
                ],
                "minimum_should_match": 1,
            }
        },
    )


@router.get("/health")
def search_health():
    try:
        client = create_search_client()

        if not client.ping():
            return {
                "status": "offline",
                "available": False,
                "message": "Elasticsearch search is unavailable.",
            }

        info = client.info()

        return {
            "status": "online",
            "available": True,
            "version": info["version"]["number"],
            "index": ANIMAL_INDEX,
        }

    except Exception as exc:
        logger.warning(
            "Optional DairyOS search unavailable: %s",
            exc,
        )

        return {
            "status": "offline",
            "available": False,
            "message": "Elasticsearch search is unavailable.",
        }


@router.get("/animals")
def search_animals(
    q: str = Query(..., min_length=1, max_length=100),
):
    term = q.strip()

    try:
        client = create_search_client()

        if not client.ping():
            raise HTTPException(
                status_code=503,
                detail="Animal search is temporarily unavailable.",
            )

        if not client.indices.exists(index=ANIMAL_INDEX):
            return {
                "query": term,
                "total": 0,
                "results": [],
                "message": "Animal search index has not been populated.",
            }

        exact = _exact_identifier_search(
            client,
            term,
        )

        if int(exact["hits"]["total"]["value"]) > 0:
            return _hits_payload(term, exact)

        general = _general_search(
            client,
            term,
        )

        return _hits_payload(term, general)

    except HTTPException:
        raise

    except Exception as exc:
        logger.warning(
            "DairyOS animal search failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=503,
            detail="Animal search is temporarily unavailable.",
        ) from exc