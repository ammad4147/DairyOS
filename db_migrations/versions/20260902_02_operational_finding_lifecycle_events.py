"""Add immutable operational finding lifecycle events.

Revision ID: 20260902_02
Revises: 20260902_01
"""
from alembic import op
import sqlalchemy as sa

from dairyos.data.database.destructive_guards import (
    install_destructive_guards,
)


revision = "20260902_02"
down_revision = "20260902_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operational_finding_lifecycle_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("finding_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("operator", sa.String(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("linked_event_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["operational_findings.finding_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["linked_event_id"],
            ["operational_finding_lifecycle_events.id"],
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_finding_lifecycle_finding_id",
        "operational_finding_lifecycle_events",
        ["finding_id"],
    )
    op.create_index(
        "ix_finding_lifecycle_event_type",
        "operational_finding_lifecycle_events",
        ["event_type"],
    )
    op.create_index(
        "ix_finding_lifecycle_occurred_at",
        "operational_finding_lifecycle_events",
        ["occurred_at"],
    )
    op.create_index(
        "ix_finding_lifecycle_linked_event_id",
        "operational_finding_lifecycle_events",
        ["linked_event_id"],
    )

    bind = op.get_bind()
    lifecycle = sa.table(
        "operational_finding_lifecycle_events",
        sa.column("finding_id", sa.String()),
        sa.column("event_type", sa.String()),
        sa.column("occurred_at", sa.DateTime()),
        sa.column("operator", sa.String()),
        sa.column("note", sa.String()),
        sa.column("linked_event_id", sa.Integer()),
    )

    rows = bind.execute(
        sa.text(
            """
            SELECT
                finding_id,
                detail,
                raised_at,
                acknowledged_at,
                acknowledged_by,
                resolved_at,
                resolved_by,
                resolution_note,
                reinstated_at,
                reinstated_by,
                reinstate_reason
            FROM operational_findings
            """
        )
    ).mappings()

    for finding in rows:
        snapshots = [
            ("RAISED", finding["raised_at"], None, finding["detail"]),
            (
                "ACKNOWLEDGED",
                finding["acknowledged_at"],
                finding["acknowledged_by"],
                None,
            ),
            (
                "RESOLVED",
                finding["resolved_at"],
                finding["resolved_by"],
                finding["resolution_note"],
            ),
            (
                "REINSTATED",
                finding["reinstated_at"],
                finding["reinstated_by"],
                finding["reinstate_reason"],
            ),
        ]
        for event_type, occurred_at, operator, note in sorted(
            [item for item in snapshots if item[1] is not None],
            key=lambda item: item[1],
        ):
            bind.execute(
                lifecycle.insert().values(
                    finding_id=finding["finding_id"],
                    event_type=event_type,
                    occurred_at=occurred_at,
                    operator=operator,
                    note=note,
                    linked_event_id=None,
                )
            )

    # Apply the certified destructive-operation guard to the new audit table.
    install_destructive_guards(bind)


def downgrade() -> None:
    op.drop_index(
        "ix_finding_lifecycle_linked_event_id",
        table_name="operational_finding_lifecycle_events",
    )
    op.drop_index(
        "ix_finding_lifecycle_occurred_at",
        table_name="operational_finding_lifecycle_events",
    )
    op.drop_index(
        "ix_finding_lifecycle_event_type",
        table_name="operational_finding_lifecycle_events",
    )
    op.drop_index(
        "ix_finding_lifecycle_finding_id",
        table_name="operational_finding_lifecycle_events",
    )
    op.drop_table("operational_finding_lifecycle_events")
