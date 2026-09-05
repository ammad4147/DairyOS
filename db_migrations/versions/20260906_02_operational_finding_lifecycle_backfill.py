"""Backfill missing OperationalFinding RAISED lifecycle events.

Revision ID: 20260906_02
Revises: 20260906_01
"""
import sqlalchemy as sa
from alembic import op

from dairyos.data.database.destructive_guards import install_destructive_guards

revision = "20260906_02"
down_revision = "20260906_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    rows = bind.execute(
        sa.text(
            """
            SELECT
                f.finding_id,
                f.raised_at,
                f.detail
            FROM operational_findings f
            WHERE NOT EXISTS (
                SELECT 1
                FROM operational_finding_lifecycle_events e
                WHERE e.finding_id = f.finding_id
                  AND e.event_type = 'RAISED'
            )
            ORDER BY f.raised_at, f.finding_id
            """
        )
    ).mappings().all()

    for row in rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO operational_finding_lifecycle_events
                    (finding_id, event_type, occurred_at, operator, note, linked_event_id)
                VALUES
                    (:finding_id, 'RAISED', :occurred_at, NULL, :note, NULL)
                """
            ),
            {
                "finding_id": row["finding_id"],
                "occurred_at": row["raised_at"],
                "note": row["detail"],
            },
        )

    install_destructive_guards(bind)


def downgrade() -> None:
    raise RuntimeError(
        "Operational finding lifecycle backfill is immutable audit history and cannot be destructively downgraded."
    )
