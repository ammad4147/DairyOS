import json
import os
import tempfile
from dairyos.platform.paths import resolve_storage_file
from pathlib import Path

from dairyos.farm.herd.models.animal_operational_state import (
    AnimalOperationalState,
)


class AnimalOperationalStateRepository:
    """
    Persistence boundary for animal operational read models.

    Stores current projected animal condition.

    Historical operational events remain
    owned by the event journal.

    Repository provides durable materialized state
    recovery between application restarts.
    """

    def __init__(
        self,
        storage_path=None,
    ):
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else resolve_storage_file(
                "animal_operational_states.json"
            )
        )

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._states = {}

        self._load()

    def save(
        self,
        state: AnimalOperationalState,
    ):
        self._states[state.animal_id] = state
        self._persist()
        return state

    def save_state(
        self,
        state: AnimalOperationalState,
    ):
        return self.save(state)

    def get(
        self,
        animal_id: str,
    ) -> AnimalOperationalState | None:
        return self._states.get(animal_id)

    def load(
        self,
        animal_id: str,
    ) -> AnimalOperationalState | None:
        return self.get(animal_id)

    def get_all(
        self,
    ) -> list[AnimalOperationalState]:
        return list(self._states.values())

    def clear(self):
        """
        Remove the materialized projection.

        The event journal remains untouched. This is used by
        deterministic recovery before replaying the journal.
        """
        self._states = {}
        self._persist()

    def _persist(self):
        data = [
            state.to_dict()
            for state in self._states.values()
        ]

        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f"{self.storage_path.name}.",
            suffix=".tmp",
            dir=self.storage_path.parent,
            text=True,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(
                file_descriptor,
                "w",
                encoding="utf-8",
                newline="\n",
            ) as file:
                json.dump(data, file, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.storage_path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def _load(self):
        if not self.storage_path.exists():
            return

        try:
            with open(
                self.storage_path,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            # This is a rebuildable read model. The event journal remains the
            # authority, so an unreadable projection must not block startup or
            # recovery; the next replay will replace it atomically.
            self._states = {}
            return

        try:
            for item in data:
                state = AnimalOperationalState.from_dict(item)

                self._states[state.animal_id] = state
        except (TypeError, ValueError, KeyError):
            # Treat partially malformed projection content like a corrupt
            # projection rather than exposing a mixed, unverifiable state.
            self._states = {}
