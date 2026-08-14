"""Operational Finding entity (AA-013 §4, D-UI-5).

Revision ID: 20260814_05
Revises: 20260814_04

The single cross-cutting entity behind the dashboard action queue, every
section's alert list, and navigation count badges. See
`src/dairyos/data/models/operational_finding.py` for the full design
rationale and `src/dairyos/api/operational_findings.py` for the lifecycle
endpoints.

Follows the self-healing column-repair pattern established on 20260814_03
and reused on 20260814_04: a table name existing is never treated as proof
it already has the right shape.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260814_05"
down_revision = "20260814_04"
branch_labels = None
depends_on = None


FINDINGS_TABLE = "operational_findings"


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _existing_columns(name: str) -> set[str]:
    return {c["name"] for c in _inspector().get_columns(name)}


_EXPECTED_COLUMNS = {
    "finding_id": sa.Column("finding_id", sa.String(), nullable=True),
    "source_module": sa.Column("source_module", sa.String(), nullable=True),
    "subject_type": sa.Column("subject_type", sa.String(), nullable=True),
    "subject_id": sa.Column("subject_id", sa.String(), nullable=True),
    "severity": sa.Column("severity", sa.String(), nullable=True),
    "title": sa.Column("title", sa.String(), nullable=True),
    "detail": sa.Column("detail", sa.String(), nullable=True),
    "status": sa.Column("status", sa.String(), nullable=True),
    "route": sa.Column("route", sa.String(), nullable=True),
    "dedupe_key": sa.Column("dedupe_key", sa.String(), nullable=True),
    "observation_count": sa.Column("observation_count", sa.Integer(), nullable=True),
    "raised_at": sa.Column("raised_at", sa.DateTime(), nullable=True),
    "last_observed_at": sa.Column("last_observed_at", sa.DateTime(), nullable=True),
    "acknowledged_at": sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
    "acknowledged_by": sa.Column("acknowledged_by", sa.String(), nullable=True),
    "resolved_at": sa.Column("resolved_at", sa.DateTime(), nullable=True),
    "resolved_by": sa.Column("resolved_by", sa.String(), nullable=True),
    "resolution_note": sa.Column("resolution_note", sa.String(), nullable=True),
}


def upgrade() -> None:
    if not _has_table(FINDINGS_TABLE):
        op.create_table(
            FINDINGS_TABLE,
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("finding_id", sa.String(), nullable=False, unique=True),
            sa.Column("source_module", sa.String(), nullable=False),
            sa.Column("subject_type", sa.String(), nullable=True),
            sa.Column("subject_id", sa.String(), nullable=True),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("detail", sa.String(), nullable=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("route", sa.String(), nullable=True),
            sa.Column("dedupe_key", sa.String(), nullable=True),
            sa.Column("observation_count", sa.Integer(), nullable=False),
            sa.Column("raised_at", sa.DateTime(), nullable=False),
            sa.Column("last_observed_at", sa.DateTime(), nullable=False),
            sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
            sa.Column("acknowledged_by", sa.String(), nullable=True),
            sa.Column("resolved_at", sa.DateTime(), nullable=True),
            sa.Column("resolved_by", sa.String(), nullable=True),
            sa.Column("resolution_note", sa.String(), nullable=True),
        )
        with op.batch_alter_table(FINDINGS_TABLE) as batch:
            batch.create_index("ix_operational_findings_finding_id", ["finding_id"])
            batch.create_index("ix_operational_findings_source_module", ["source_module"])
            batch.create_index("ix_operational_findings_subject_id", ["subject_id"])
            batch.create_index("ix_operational_findings_status", ["status"])
            batch.create_index("ix_operational_findings_dedupe_key", ["dedupe_key"])
    else:
        # A table with this name already existing is not proof it has the
        # right shape -- add whatever of the expected columns are missing
        # rather than assuming (the lesson from 20260814_03).
        existing = _existing_columns(FINDINGS_TABLE)
        for name, column in _EXPECTED_COLUMNS.items():
            if name not in existing:
                op.add_column(FINDINGS_TABLE, column.copy())


def downgrade() -> None:
    if _has_table(FINDINGS_TABLE):
        op.drop_table(FINDINGS_TABLE)
