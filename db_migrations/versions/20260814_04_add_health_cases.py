"""HealthCase entity (G5.1).

Revision ID: 20260814_04
Revises: 20260814_03

Before this migration, `GET /health` was a 4-line system heartbeat, not
animal data. The real health surface -- `HealthObservation` -- had no
status-transition endpoint: an observation could be recorded, but nothing
modeled "this animal is currently being treated for X, watch it until Y,
here's how it was resolved." Decision (build-spec Session 5,
DairyOS_Build_Specification.md Ch.5): build a real `HealthCase` entity, its
own `HL-YYMMDD-NNN` ID, wrapping observations[] + diagnosis + treatments[] +
withdrawal_until + follow_up_due_at + resolution. Resolution is an explicit
operator action.

`health_observation` and `treatment_record` each gain a nullable
`health_case_id` column so existing write paths keep working exactly as
before (unlinked); linking is optional at write time.

Learned the hard way on 20260814_03 (the identity/RBAC migration): a table
name existing is not proof it has the right shape -- a stray same-named
table from an earlier, unrelated experiment silently stranded that
migration's own no-op guard. Every DDL step here checks actual columns
before assuming a pre-existing object already matches, not just table
presence.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260814_04"
down_revision = "20260814_03"
branch_labels = None
depends_on = None


CASES_TABLE = "health_cases"


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _existing_columns(name: str) -> set[str]:
    return {c["name"] for c in _inspector().get_columns(name)}


_EXPECTED_CASE_COLUMNS = {
    "case_id": sa.Column("case_id", sa.String(), nullable=True),
    "animal_id": sa.Column("animal_id", sa.String(), nullable=True),
    "severity": sa.Column("severity", sa.String(), nullable=True),
    "diagnosis": sa.Column("diagnosis", sa.String(), nullable=True),
    "notes": sa.Column("notes", sa.String(), nullable=True),
    "status": sa.Column("status", sa.String(), nullable=True),
    "opened_at": sa.Column("opened_at", sa.DateTime(), nullable=True),
    "opened_by": sa.Column("opened_by", sa.String(), nullable=True),
    "follow_up_due_at": sa.Column("follow_up_due_at", sa.DateTime(), nullable=True),
    "withdrawal_until": sa.Column("withdrawal_until", sa.DateTime(), nullable=True),
    "resolution": sa.Column("resolution", sa.String(), nullable=True),
    "resolved_at": sa.Column("resolved_at", sa.DateTime(), nullable=True),
    "resolved_by": sa.Column("resolved_by", sa.String(), nullable=True),
}


def _ensure_health_case_id_column(table: str) -> None:
    if table not in _inspector().get_table_names():
        # The parent table not existing is out of scope for this migration
        # (it's owned by an earlier revision); nothing to add a column to.
        return

    if "health_case_id" not in _existing_columns(table):
        op.add_column(table, sa.Column("health_case_id", sa.Integer(), nullable=True))


def upgrade() -> None:
    if not _has_table(CASES_TABLE):
        op.create_table(
            CASES_TABLE,
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("case_id", sa.String(), nullable=False, unique=True),
            sa.Column("animal_id", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("diagnosis", sa.String(), nullable=True),
            sa.Column("notes", sa.String(), nullable=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("opened_at", sa.DateTime(), nullable=False),
            sa.Column("opened_by", sa.String(), nullable=True),
            sa.Column("follow_up_due_at", sa.DateTime(), nullable=True),
            sa.Column("withdrawal_until", sa.DateTime(), nullable=True),
            sa.Column("resolution", sa.String(), nullable=True),
            sa.Column("resolved_at", sa.DateTime(), nullable=True),
            sa.Column("resolved_by", sa.String(), nullable=True),
        )
    else:
        # A "health_cases" table already existing here is not proof it has
        # the right shape -- add whatever of the expected columns are
        # missing rather than assuming.
        existing = _existing_columns(CASES_TABLE)
        for name, column in _EXPECTED_CASE_COLUMNS.items():
            if name not in existing:
                op.add_column(CASES_TABLE, column.copy())

    _ensure_health_case_id_column("health_observation")
    _ensure_health_case_id_column("treatment_record")


def downgrade() -> None:
    for table in ("health_observation", "treatment_record"):
        if table in _inspector().get_table_names() and "health_case_id" in _existing_columns(table):
            op.drop_column(table, "health_case_id")

    if _has_table(CASES_TABLE):
        op.drop_table(CASES_TABLE)
