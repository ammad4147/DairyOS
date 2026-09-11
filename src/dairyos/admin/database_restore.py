"""Database-only recovery, with a full rollback point and rebuilt read models."""

from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dairyos.application.file_projection_rebuilder import FileProjectionRebuilder
from dairyos.data.database.backup import restore_backup
from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)
from dairyos.farm.herd.services.animal_event_projection import AnimalEventProjection
from dairyos.farm.inputs.repository.operational_input_repository import (
    OperationalInputRepository,
)
from dairyos.lifecycle.manager import LifecycleError
from dairyos.lifecycle.restore import restore_snapshot
from dairyos.runtime.persistent_event_journal import PersistentEventJournal


def rebuild_file_projections(manager) -> None:
    """Never retain future operational projections after an older DB restore.

    Only the two event-owned JSON read models are regenerated. Local Admin
    credentials, logs, attachments and all other non-database files stay put.
    """
    engine = create_engine(manager.database_url)
    try:
        storage = manager.data_root / "storage"
        input_path = storage / "operational_inputs.json"
        animal_state_path = storage / "animal_operational_states.json"
        # These files are rebuildable projections. The rebuilder reads the
        # journal into a staged pair and promotes only after replay succeeds;
        # never delete the last known-good projections before that transaction
        # has reached its promotion point.
        inputs = OperationalInputRepository(input_path)
        states = AnimalOperationalStateRepository(
            animal_state_path
        )
        FileProjectionRebuilder(
            event_journal=PersistentEventJournal(sessionmaker(bind=engine)),
            operational_input_repository=inputs,
            animal_operational_state_repository=states,
            animal_event_projection=AnimalEventProjection(repository=states),
        ).rebuild()
    finally:
        engine.dispose()


def restore_database_only(manager, dump: Path) -> None:
    from dairyos.admin.service import _record_database_checksum, _verify_backup_directory

    rollback = manager.backup(label="pre-database-restore", require_database=True)
    _record_database_checksum(rollback)
    _verify_backup_directory(rollback, require_database=True)
    restored = False
    try:
        restore_backup(manager.database_url, dump, allow_environment_password_override=False)
        restored = True
        rebuild_file_projections(manager)
        manager.validate(require_database=True)
    except Exception as exc:
        if restored:
            try:
                restore_snapshot(manager, rollback)
            except Exception as rollback_exc:
                raise LifecycleError(f"Database recovery failed and rollback was incomplete: {rollback_exc}") from exc
        raise LifecycleError(f"Database recovery failed; pre-restore state retained or restored: {exc}") from exc
