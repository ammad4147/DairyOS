"""
Build or refresh the optional DairyOS Elasticsearch animal search projection.

Usage:

    python -m dairyos.api.index_animals
    python -m dairyos.api.index_animals --rebuild

The default operation is non-destructive and upserts every authoritative
Animal record.

--rebuild deletes only the disposable Elasticsearch animal-search index and
recreates it. It never modifies PostgreSQL or DairyOS animal data.
"""

from __future__ import annotations

import argparse

from dairyos.api.search import (
    ANIMAL_INDEX,
    animal_document,
    create_search_client,
    ensure_animal_index,
)
from dairyos.data.repositories.repository_factory import RepositoryFactory


def index_animals(*, rebuild: bool = False) -> int:
    client = create_search_client()

    if not client.ping():
        raise RuntimeError(
            "Elasticsearch is not available. "
            "Start the optional search service before indexing."
        )

    if rebuild and client.indices.exists(index=ANIMAL_INDEX):
        client.indices.delete(index=ANIMAL_INDEX)

    ensure_animal_index(client)

    factory = RepositoryFactory.create()

    try:
        animals = factory.animal().get_all()

        indexed = 0

        for animal in animals:
            animal_id = str(animal.animal_id)

            client.index(
                index=ANIMAL_INDEX,
                id=animal_id,
                document=animal_document(animal),
            )

            indexed += 1

        client.indices.refresh(index=ANIMAL_INDEX)

        return indexed

    finally:
        factory.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Index authoritative DairyOS animal records "
            "into the optional Elasticsearch search projection."
        )
    )

    parser.add_argument(
        "--rebuild",
        action="store_true",
        help=(
            "Recreate only the disposable Elasticsearch "
            "animal index before indexing."
        ),
    )

    args = parser.parse_args()

    count = index_animals(
        rebuild=args.rebuild,
    )

    print(
        f"DairyOS animal search projection: "
        f"{count} animal record(s) indexed."
    )


if __name__ == "__main__":
    main()