from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import inspect, text

from dairyos.api.dashboard_attention import project_vaccination_schedule
from dairyos.api.dependencies import get_container
from dairyos.assistant.knowledge import GroundedAssistant
from dairyos.data.database.automatic_backups import read_backup_health
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)
from dairyos.platform import paths

router = APIRouter(tags=["Health"])


SYSTEM_HEALTH_SCHEMA_VERSION = 2
BACKUP_STALE_AFTER = timedelta(hours=30)

_REQUIRED_TABLES = frozenset(
    {
        "app_settings",
        "animal",
        "breeding_records",
        "event_journal",
        "feed_record",
        "financial_transactions",
        "health_cases",
        "health_observation",
        "milk_production",
        "operational_events",
        "operational_projection_outbox",
        "operational_states",
        "operational_write",
        "treatment_record",
    }
)

_PERSISTENCE_TABLES = (
    ("animal persistence", "animal"),
    ("milk persistence", "milk_production"),
    ("feed persistence", "feed_record"),
    ("finance persistence", "financial_transactions"),
    ("health observation persistence", "health_observation"),
    ("health case persistence", "health_cases"),
    ("treatment persistence", "treatment_record"),
    ("breeding persistence", "breeding_records"),
    ("event journal persistence", "event_journal"),
    ("operational write receipts", "operational_write"),
    ("projection outbox persistence", "operational_projection_outbox"),
)


def _health_check(
    name: str, status: str, detail: str, **evidence: Any
) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name, "status": status, "detail": detail}
    payload.update(evidence)
    return payload


def _as_utc_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif value:
        try:
            parsed = datetime.fromisoformat(str(value))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _backup_health_check() -> dict[str, Any]:
    """Inspect backup evidence without creating directories or running a dump."""
    root = paths.data_root(create=False)
    health = dict(read_backup_health(root))
    backup_status = str(health.get("status") or "NEVER_RUN").upper()
    last_successful = health.get("last_successful_backup")
    last_time = _as_utc_datetime(last_successful)
    age_hours = (
        round(max((datetime.now(UTC) - last_time).total_seconds(), 0) / 3600, 2)
        if last_time is not None
        else None
    )
    primary_value = health.get("primary")
    primary_present = bool(
        isinstance(primary_value, str) and primary_value.strip() and Path(primary_value).is_file()
    )
    archive_verified = bool(health.get("archive_verified"))
    physically_redundant = bool(health.get("physically_redundant"))
    restore_verified = bool(health.get("restore_verified"))

    evidence = {
        "backup_status": backup_status,
        "last_successful_backup": last_successful,
        "age_hours": age_hours,
        "archive_verified": archive_verified,
        "primary_artifact_present": primary_present,
        "physically_redundant": physically_redundant,
        "restore_verified": restore_verified,
    }
    if backup_status == "NEVER_RUN":
        return _health_check(
            "backup protection",
            "WARNING",
            "No successful automatic backup is recorded yet; the health check did not create one.",
            **evidence,
        )
    if backup_status in {"FAILED", "INVALID_HEALTH_RECORD"}:
        return _health_check(
            "backup protection",
            "FAIL",
            f"Automatic backup protection reports {backup_status}; do not treat this installation as recoverable until it is repaired and verified.",
            **evidence,
        )
    if not primary_present or not archive_verified:
        return _health_check(
            "backup protection",
            "FAIL",
            "Backup metadata is present but the verified primary artifact or archive verification is missing.",
            **evidence,
        )
    if age_hours is not None and age_hours > BACKUP_STALE_AFTER.total_seconds() / 3600:
        return _health_check(
            "backup protection",
            "WARNING",
            f"The last successful backup is {age_hours} hour(s) old, beyond the {int(BACKUP_STALE_AFTER.total_seconds() / 3600)}-hour freshness target.",
            **evidence,
        )
    if backup_status == "DEGRADED" or not physically_redundant or not restore_verified:
        reasons = []
        if backup_status == "DEGRADED" or not physically_redundant:
            reasons.append("no independently redundant copy is confirmed")
        if not restore_verified:
            reasons.append("a recent isolated restore proof is not recorded")
        return _health_check(
            "backup protection",
            "WARNING",
            "Backup creation and archive verification passed, but " + " and ".join(reasons) + ".",
            **evidence,
        )
    return _health_check(
        "backup protection",
        "PASS",
        "The latest automatic backup is present and archive-verified with independent recovery protection recorded.",
        **evidence,
    )


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _vaccination_events(container):
    rows = []
    for event in container.event_journal.all_events():
        if event.name != "OperationalInputReceived":
            continue
        payload = dict(event.payload or {})
        if str(payload.get("input_type") or "").lower() != "vaccination":
            continue
        if str(payload.get("status") or "COMPLETED").upper() == "VOID":
            continue
        rows.append(payload)
    return rows


@router.get("/health")
def health():
    return {"system": "DairyOS", "status": "healthy", "runtime": "active"}


@router.get("/farm/health/summary")
def get_health_summary(container=Depends(get_container)):  # noqa: B008
    factory = container.repository_factory
    today = OperationalDateAuthority(repository_factory=factory).current_date()

    cases = factory.health_cases().get_all()
    active = [
        case
        for case in cases
        if str(getattr(case, "status", "") or "").upper() != "RESOLVED"
    ]
    active_animals = {
        str(getattr(case, "animal_id", ""))
        for case in active
        if getattr(case, "animal_id", None)
    }

    treatments = factory.treatment().get_all()
    withdrawal_animals = set()
    for row in treatments:
        animal_id = str(getattr(row, "animal_id", "") or "")
        treated_on = _as_date(getattr(row, "treated_at", None))
        withdrawal_until = _as_date(
            getattr(row, "milk_withdrawal_until", None)
        )

        if (
            animal_id
            and treated_on is not None
            and withdrawal_until is not None
            and treated_on <= today <= withdrawal_until
        ):
            withdrawal_animals.add(animal_id)

    followups_due = 0
    for case in active:
        due = _as_date(getattr(case, "follow_up_due_at", None))
        if due is not None and due <= today:
            followups_due += 1

    return {
        "activeClinicalCases": len(active),
        "activeSickAnimals": len(active_animals),
        "withdrawalAnimals": len(withdrawal_animals),
        "followupsDue": followups_due,
        "data_status": "LIVE_PERSISTED_DATA",
    }


@router.get("/farm/system-health")
def get_system_health(container=Depends(get_container)):  # noqa: B008
    """Run a strictly read-only DairyOS integrity and readiness check.

    The check is intentionally diagnostic rather than corrective.  It does not
    migrate, repair, back up, reset, compact, delete, or otherwise mutate the
    farm database or its files.  Database activity is limited to metadata and
    SELECT statements on a dedicated session.  PostgreSQL is additionally
    instructed to reject writes for the duration of that diagnostic transaction,
    so System Health cannot share or roll back an operational write transaction.
    """
    factory = RepositoryFactory.create()
    checks: list[dict[str, Any]] = []
    session = factory.session
    tables: set[str] = set()
    inspector = None
    checked_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    if session is None:
        checks.append(
            _health_check(
                "database",
                "FAIL",
                "Database session is not available; live integrity cannot be verified.",
            )
        )
    else:
        try:
            bind = session.get_bind()
            if (
                getattr(bind, "dialect", None) is not None
                and bind.dialect.name == "postgresql"
            ):
                session.execute(text("SET TRANSACTION READ ONLY"))
            session.execute(text("SELECT 1"))
            checks.append(
                _health_check(
                    "database",
                    "PASS",
                    "Database connection is responsive; no mutation was performed.",
                )
            )
        except Exception as exc:  # noqa: BLE001
            checks.append(
                _health_check(
                    "database",
                    "FAIL",
                    f"Database query failed ({type(exc).__name__}); live integrity cannot be verified.",
                )
            )

        try:
            inspector = inspect(session.bind)
            tables = set(inspector.get_table_names())
            missing = sorted(_REQUIRED_TABLES - tables)
            checks.append(
                _health_check(
                    "schema",
                    "FAIL" if missing else "PASS",
                    (
                        "Missing required tables: " + ", ".join(missing)
                        if missing
                        else "All current DairyOS operational, clinical, event and Assistant-read tables are present."
                    ),
                    table_count=len(tables),
                    required_table_count=len(_REQUIRED_TABLES),
                    missing_tables=missing,
                )
            )
        except Exception as exc:  # noqa: BLE001
            checks.append(
                _health_check(
                    "schema",
                    "FAIL",
                    f"Schema inspection failed ({type(exc).__name__}); schema authority cannot be verified.",
                )
            )

        if inspector is not None:
            expected_columns = {
                "event_journal": {"id", "event_id", "event_type", "timestamp", "payload"},
                "operational_projection_outbox": {"request_id", "journal_id", "status"},
                "health_observation": {"id", "animal_id", "observed_at", "health_case_id"},
                "health_cases": {"id", "case_id", "animal_id", "status"},
                "treatment_record": {"id", "animal_id", "treated_at", "health_case_id"},
            }
            missing_columns: list[str] = []
            try:
                for table, required_columns in expected_columns.items():
                    if table not in tables:
                        continue
                    actual = {
                        str(column["name"])
                        for column in inspector.get_columns(table)
                    }
                    missing_columns.extend(
                        f"{table}.{column}"
                        for column in sorted(required_columns - actual)
                    )
                checks.append(
                    _health_check(
                        "schema columns",
                        "FAIL" if missing_columns else "PASS",
                        (
                            "Missing required columns: " + ", ".join(missing_columns)
                            if missing_columns
                            else "Canonical clinical, event-journal and outbox columns are present."
                        ),
                        missing_columns=missing_columns,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                checks.append(
                    _health_check(
                        "schema columns",
                        "FAIL",
                        f"Column inspection failed ({type(exc).__name__}); schema details cannot be verified.",
                    )
                )

        for name, table in _PERSISTENCE_TABLES:
            if table not in tables:
                continue
            try:
                count = int(
                    session.execute(
                        text(f'SELECT count(*) FROM "{table}"')
                    ).scalar_one()
                )
                checks.append(
                    _health_check(
                        name,
                        "PASS",
                        f"{count} persisted row(s) found; no mutation performed.",
                        table=table,
                        row_count=count,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                checks.append(
                    _health_check(
                        name,
                        "FAIL",
                        f"Read failed ({type(exc).__name__}); persistence cannot be verified.",
                        table=table,
                    )
                )

        if {"event_journal", "operational_projection_outbox"}.issubset(tables):
            try:
                orphaned = int(
                    session.execute(
                        text(
                            'SELECT count(*) FROM "operational_projection_outbox" o '
                            'LEFT JOIN "event_journal" e ON e.id = o.journal_id '
                            "WHERE e.id IS NULL"
                        )
                    ).scalar_one()
                )
                pending = int(
                    session.execute(
                        text(
                            'SELECT count(*) FROM "operational_projection_outbox" '
                            "WHERE upper(coalesce(status, '')) <> 'DELIVERED'"
                        )
                    ).scalar_one()
                )
                projection_status = (
                    "FAIL" if orphaned else "WARNING" if pending else "PASS"
                )
                checks.append(
                    _health_check(
                        "event projections",
                        projection_status,
                        f"{orphaned} orphaned projection event(s); {pending} pending or failed delivery event(s).",
                        orphaned_count=orphaned,
                        pending_count=pending,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                checks.append(
                    _health_check(
                        "event projections",
                        "FAIL",
                        f"Projection linkage check failed ({type(exc).__name__}); orphan status cannot be verified.",
                    )
                )
        else:
            checks.append(
                _health_check(
                    "event projections",
                    "FAIL",
                    "Canonical event journal and projection outbox tables are not both available; orphan status cannot be verified.",
                )
            )

        relation_checks = (
            (
                "health observation animal links",
                (
                    'SELECT count(*) FROM "health_observation" h '
                    'LEFT JOIN "animal" a ON a.animal_id = h.animal_id '
                    "WHERE a.animal_id IS NULL"
                ),
                "health_observation rows",
            ),
            (
                "health case animal links",
                (
                    'SELECT count(*) FROM "health_cases" h '
                    'LEFT JOIN "animal" a ON a.animal_id = h.animal_id '
                    "WHERE a.animal_id IS NULL"
                ),
                "health_cases rows",
            ),
            (
                "treatment animal links",
                (
                    'SELECT count(*) FROM "treatment_record" t '
                    'LEFT JOIN "animal" a ON a.animal_id = t.animal_id '
                    "WHERE a.animal_id IS NULL"
                ),
                "treatment_record rows",
            ),
            (
                "health observation case links",
                (
                    'SELECT count(*) FROM "health_observation" h '
                    'LEFT JOIN "health_cases" c ON c.id = h.health_case_id '
                    "WHERE h.health_case_id IS NOT NULL AND c.id IS NULL"
                ),
                "health_observation case links",
            ),
            (
                "treatment case links",
                (
                    'SELECT count(*) FROM "treatment_record" t '
                    'LEFT JOIN "health_cases" c ON c.id = t.health_case_id '
                    "WHERE t.health_case_id IS NOT NULL AND c.id IS NULL"
                ),
                "treatment case links",
            ),
            (
                "projection receipt links",
                (
                    'SELECT count(*) FROM "operational_projection_outbox" o '
                    'LEFT JOIN "operational_write" w ON w.request_id = o.request_id '
                    "WHERE w.request_id IS NULL"
                ),
                "operational_projection_outbox receipts",
            ),
        )
        for name, statement, subject in relation_checks:
            try:
                required_tables = {
                    "health observation animal links": {"health_observation", "animal"},
                    "health case animal links": {"health_cases", "animal"},
                    "treatment animal links": {"treatment_record", "animal"},
                    "health observation case links": {"health_observation", "health_cases"},
                    "treatment case links": {"treatment_record", "health_cases"},
                    "projection receipt links": {"operational_projection_outbox", "operational_write"},
                }[name]
                if not required_tables.issubset(tables):
                    continue
                orphaned = int(session.execute(text(statement)).scalar_one())
                checks.append(
                    _health_check(
                        name,
                        "FAIL" if orphaned else "PASS",
                        f"{orphaned} orphaned {subject}; no repair was attempted.",
                        orphaned_count=orphaned,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                checks.append(
                    _health_check(
                        name,
                        "FAIL",
                        f"Relationship check failed ({type(exc).__name__}); orphan status cannot be verified.",
                    )
                )

        try:
            checks.append(_backup_health_check())
        except Exception as exc:  # noqa: BLE001
            checks.append(
                _health_check(
                    "backup protection",
                    "FAIL",
                    f"Backup protection record could not be read ({type(exc).__name__}); no backup was started.",
                )
            )

        try:
            location = paths.describe()
            data_root = Path(location["data_root"])
            legacy_storage = location.get("legacy_storage_in_use") == "True"
            if legacy_storage:
                layout_status = "FAIL"
                layout_detail = "Legacy farm storage is present without an explicit managed-data migration; no path was selected or moved."
            elif not data_root.exists():
                layout_status = "WARNING"
                layout_detail = "The managed data root does not exist yet; the health check did not create it."
            else:
                layout_status = "PASS"
                layout_detail = "Managed farm-data root is resolved outside the installation directory."
            checks.append(
                _health_check(
                    "data layout",
                    layout_status,
                    layout_detail,
                    data_root=str(data_root),
                    legacy_storage_in_use=legacy_storage,
                )
            )
        except Exception as exc:  # noqa: BLE001
            checks.append(
                _health_check(
                    "data layout",
                    "FAIL",
                    f"Managed data-root inspection failed ({type(exc).__name__}); storage authority cannot be verified.",
                )
            )

        try:
            coverage = GroundedAssistant().coverage()
            domains = coverage.get("domains") or []
            items = int(coverage.get("items") or 0)
            assistant_status = (
                "PASS"
                if items > 0 and "health-and-veterinary" in domains
                else "FAIL"
            )
            checks.append(
                _health_check(
                    "AI Assistant knowledge",
                    assistant_status,
                    f"Local vector knowledge index loaded {items} item(s); clinical reference domain is {'present' if 'health-and-veterinary' in domains else 'missing'}.",
                    indexed_items=items,
                    clinical_domain_present="health-and-veterinary" in domains,
                    retrieval=coverage.get("retrieval"),
                )
            )
        except Exception as exc:  # noqa: BLE001
            checks.append(
                _health_check(
                    "AI Assistant knowledge",
                    "FAIL",
                    f"Local Assistant knowledge index could not be loaded ({type(exc).__name__}).",
                )
            )

    runtime_started = bool(getattr(container, "started", False))
    checks.append(
        _health_check(
            "application runtime",
            "PASS" if runtime_started else "WARNING",
            (
                "Application runtime is active."
                if runtime_started
                else "Application runtime is not marked active; database checks still ran without changing data."
            ),
            started=runtime_started,
        )
    )

    factory.close()

    counts = {
        status: sum(1 for item in checks if item.get("status") == status)
        for status in ("PASS", "WARNING", "FAIL")
    }
    overall = (
        "FAIL"
        if counts["FAIL"]
        else "WARNING"
        if counts["WARNING"]
        else "PASS"
    )
    return {
        "system": "DairyOS",
        "health_schema_version": SYSTEM_HEALTH_SCHEMA_VERSION,
        "checked_at": checked_at,
        "overall": overall,
        "read_only": True,
        "data_status": "LIVE_PERSISTED_DATA_READ_ONLY",
        "summary": counts,
        "checks": checks,
        "safety": "Diagnostic reads only; no database row, schema, backup, setting or farm file was changed.",
    }


@router.get("/farm/vaccination/summary")
def get_vaccination_summary(container=Depends(get_container)):  # noqa: B008
    factory = container.repository_factory
    today = OperationalDateAuthority(repository_factory=factory).current_date()

    projection = project_vaccination_schedule(
        container.event_journal.all_events(),
        today,
    )
    completed = int(projection["completed"])
    schedules = list(projection["schedules"])
    overdue = int(projection["overdue"])
    due_next_30 = int(projection["due_next_30_days"])
    upcoming = schedules
    animals_with_history = set()

    for payload in _vaccination_events(container):
        animal_id = str(payload.get("animal_id") or "")
        if animal_id:
            animals_with_history.add(animal_id)

    animal_repo = getattr(container, "animal_repository", None)
    active_animals = []
    if animal_repo is not None and hasattr(animal_repo, "active_animals"):
        active_animals = list(animal_repo.active_animals())
    else:
        repo = factory.animal()
        all_animals = list(repo.get_all()) if hasattr(repo, "get_all") else []
        active_animals = [
            animal for animal in all_animals
            if getattr(animal, "active", True) is not False
        ]

    active_ids = {
        str(getattr(animal, "animal_id", ""))
        for animal in active_animals
        if getattr(animal, "animal_id", None)
    }

    return {
        "vaccinationsRecorded": completed,
        "vaccinationsOverdue": overdue,
        "vaccinationsDueNext30Days": due_next_30,
        "animalsWithNoVaccinationHistory": len(active_ids - animals_with_history),
        "upcomingVaccinations": upcoming[:50],
        "data_status": "LIVE_PERSISTED_DATA",
    }
