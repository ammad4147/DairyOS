"""Create canonical Equipment master and service history.

Revision ID: 20260816_01
Revises: 20260814_06, 20260815_01

This revision deliberately merges the two existing heads rather than
creating another independent branch. It creates the canonical Equipment
domain while retaining the previously audited milk-disposition migration.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260816_01"
down_revision = (
    "20260814_06",
    "20260815_01",
)
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(
        sa.inspect(
            op.get_bind()
        ).get_table_names()
    )


def upgrade() -> None:
    tables = _tables()

    if "equipment" not in tables:
        op.create_table(
            "equipment",
            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "equipment_id",
                sa.String(length=100),
                nullable=False,
            ),
            sa.Column(
                "name",
                sa.String(length=200),
                nullable=False,
            ),
            sa.Column(
                "category",
                sa.String(length=100),
                nullable=False,
            ),
            sa.Column(
                "farm_id",
                sa.String(length=100),
                nullable=False,
            ),
            sa.Column(
                "location",
                sa.String(length=200),
                nullable=True,
            ),
            sa.Column(
                "status",
                sa.String(length=50),
                nullable=False,
                server_default="AVAILABLE",
            ),
            sa.Column(
                "condition",
                sa.String(length=50),
                nullable=False,
                server_default="GOOD",
            ),
            sa.Column(
                "running_hours",
                sa.Float(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "commissioned_at",
                sa.DateTime(),
                nullable=True,
            ),
            sa.Column(
                "last_service_at",
                sa.DateTime(),
                nullable=True,
            ),
            sa.Column(
                "next_service_due_at",
                sa.DateTime(),
                nullable=True,
            ),
            sa.Column(
                "active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "equipment_id",
                name="uq_equipment_equipment_id",
            ),
        )

        op.create_index(
            "ix_equipment_equipment_id",
            "equipment",
            ["equipment_id"],
            unique=True,
        )

        op.create_index(
            "ix_equipment_farm_id",
            "equipment",
            ["farm_id"],
        )

        op.create_index(
            "ix_equipment_next_service_due_at",
            "equipment",
            ["next_service_due_at"],
        )

    tables = _tables()

    if "equipment_service_events" not in tables:
        op.create_table(
            "equipment_service_events",
            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "equipment_id",
                sa.String(length=100),
                nullable=False,
            ),
            sa.Column(
                "event_date",
                sa.Date(),
                nullable=False,
            ),
            sa.Column(
                "event_type",
                sa.String(length=100),
                nullable=False,
            ),
            sa.Column(
                "running_hours",
                sa.Float(),
                nullable=True,
            ),
            sa.Column(
                "status_before",
                sa.String(length=50),
                nullable=True,
            ),
            sa.Column(
                "status_after",
                sa.String(length=50),
                nullable=True,
            ),
            sa.Column(
                "operator",
                sa.String(length=200),
                nullable=True,
            ),
            sa.Column(
                "notes",
                sa.Text(),
                nullable=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["equipment_id"],
                ["equipment.equipment_id"],
                ondelete="CASCADE",
            ),
        )

        op.create_index(
            "ix_equipment_service_events_equipment_id",
            "equipment_service_events",
            ["equipment_id"],
        )

        op.create_index(
            "ix_equipment_service_events_event_date",
            "equipment_service_events",
            ["event_date"],
        )


def downgrade() -> None:
    tables = _tables()

    if "equipment_service_events" in tables:
        op.drop_index(
            "ix_equipment_service_events_event_date",
            table_name="equipment_service_events",
        )
        op.drop_index(
            "ix_equipment_service_events_equipment_id",
            table_name="equipment_service_events",
        )
        op.drop_table(
            "equipment_service_events"
        )

    if "equipment" in tables:
        op.drop_index(
            "ix_equipment_next_service_due_at",
            table_name="equipment",
        )
        op.drop_index(
            "ix_equipment_farm_id",
            table_name="equipment",
        )
        op.drop_index(
            "ix_equipment_equipment_id",
            table_name="equipment",
        )
        op.drop_table(
            "equipment"
        )
