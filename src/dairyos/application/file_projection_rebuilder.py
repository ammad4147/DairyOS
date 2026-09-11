"""Canonical reconstruction of event-owned file projections."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from dairyos.domain.events import Event
from dairyos.domain.events.operational_input_received import OperationalInputReceived
from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)
from dairyos.farm.herd.services.animal_event_projection import AnimalEventProjection
from dairyos.farm.inputs.repository.operational_input_repository import (
    OperationalInputRepository,
)


class FileProjectionRebuilder:
    """Rebuild JSON projections from the one durable event-journal authority."""

    def __init__(
        self,
        *,
        event_journal,
        operational_input_repository,
        animal_operational_state_repository,
        animal_event_projection,
    ):
        self.event_journal = event_journal
        self.operational_input_repository = operational_input_repository
        self.animal_operational_state_repository = animal_operational_state_repository
        self.animal_event_projection = animal_event_projection

    def rebuild(self) -> None:
        """Replay the journal into staged projections, then promote them.

        The journal and database are authoritative.  Rebuilding directly into
        the live JSON paths would make a replay failure indistinguishable from
        an empty farm projection.  Staging leaves the last known-good files in
        place until the complete replay has succeeded; promotion is guarded by
        rollback copies so a multi-file replacement cannot strand one half of
        the read model.
        """

        if not self._can_stage_json_projections():
            self._rebuild_in_place()
            return

        input_path = Path(self.operational_input_repository.storage_path)
        state_path = Path(self.animal_operational_state_repository.storage_path)
        stage_parent = input_path.parent
        stage_parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(
            prefix="dairyos-projection-rebuild-",
            dir=stage_parent,
        ) as temporary:
            stage_root = Path(temporary)
            staged_input_path = stage_root / input_path.name
            staged_state_path = stage_root / state_path.name
            staged_inputs = OperationalInputRepository(staged_input_path)
            staged_states = AnimalOperationalStateRepository(staged_state_path)
            staged_projection = AnimalEventProjection(repository=staged_states)
            # Ensure an empty journal still produces valid empty projections.
            staged_inputs.clear()
            staged_states.clear()

            self._replay(staged_inputs, staged_projection)
            _fsync_file(staged_input_path)
            _fsync_file(staged_state_path)
            _promote_projection_files(
                ((input_path, staged_input_path), (state_path, staged_state_path))
            )

    def _can_stage_json_projections(self) -> bool:
        return (
            isinstance(self.operational_input_repository, OperationalInputRepository)
            and isinstance(
                self.animal_operational_state_repository,
                AnimalOperationalStateRepository,
            )
            and isinstance(self.animal_event_projection, AnimalEventProjection)
            and bool(getattr(self.operational_input_repository, "storage_path", None))
            and bool(
                getattr(self.animal_operational_state_repository, "storage_path", None)
            )
        )

    def _rebuild_in_place(self) -> None:
        """Compatibility path for non-file test doubles or custom adapters."""
        self.operational_input_repository.clear()
        self.animal_operational_state_repository.clear()
        self._replay(self.operational_input_repository, self.animal_event_projection)

    def _replay(
        self,
        operational_input_repository,
        animal_event_projection,
    ) -> None:
        for entry in self.event_journal.all_entries():
            event = Event(
                name=entry.event_type,
                payload=dict(entry.payload),
                timestamp=entry.timestamp.isoformat(),
            )
            if entry.event_type == "OperationalInputReceived":
                payload = dict(entry.payload)
                operational_input_repository.save(
                    OperationalInputReceived(
                        input_type=str(payload["input_type"]),
                        payload=payload,
                        source=str(payload.get("source", "")),
                        actor=str(payload.get("actor", "")),
                        event_id=entry.event_id,
                        timestamp=entry.timestamp,
                    )
                )
            animal_event_projection.apply(event)


def _fsync_file(path: Path) -> None:
    """Flush a staged projection before it becomes visible."""
    with path.open("r+b") as stream:
        os.fsync(stream.fileno())


def _promote_projection_files(
    pairs: tuple[tuple[Path, Path], ...],
) -> None:
    """Promote several staged files while retaining rollback copies."""
    rollback_paths: list[tuple[Path, Path]] = []
    promoted: list[Path] = []
    committed = False
    try:
        for target, _staged in pairs:
            if not target.exists():
                continue
            descriptor, rollback_name = tempfile.mkstemp(
                prefix=f".{target.name}.",
                suffix=".rollback",
                dir=target.parent,
            )
            os.close(descriptor)
            rollback = Path(rollback_name)
            rollback.unlink()
            os.replace(target, rollback)
            rollback_paths.append((target, rollback))

        for target, staged in pairs:
            os.replace(staged, target)
            promoted.append(target)
        committed = True
    except Exception:
        for target in reversed(promoted):
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
        for target, rollback in reversed(rollback_paths):
            if rollback.exists():
                os.replace(rollback, target)
        raise
    finally:
        if committed:
            for _target, rollback in rollback_paths:
                rollback.unlink(missing_ok=True)
