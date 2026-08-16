"""Add animal-level veterinary non-milking directive state.

This migration introduces animal/herd state for temporary non-milking,
separate-milk handling, and permanent non-milking.

It does not alter milk disposition semantics.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260817_02"
down_revision = "20260816_02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "animal",
        sa.Column(
            "non_milking_directive",
            sa.String(),
            nullable=False,
            server_default="NONE",
        ),
    )

    op.add_column(
        "animal",
        sa.Column(
            "non_milking_since",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "animal",
        sa.Column(
            "non_milking_until",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "animal",
        sa.Column(
            "non_milking_reason",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "animal",
        sa.Column(
            "non_milking_changed_by",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "animal",
        sa.Column(
            "non_milking_restore_to_milking",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_index(
        "ix_animal_non_milking_directive",
        "animal",
        ["non_milking_directive"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_animal_non_milking_directive",
        table_name="animal",
    )

    op.drop_column(
        "animal",
        "non_milking_restore_to_milking",
    )

    op.drop_column(
        "animal",
        "non_milking_changed_by",
    )

    op.drop_column(
        "animal",
        "non_milking_reason",
    )

    op.drop_column(
        "animal",
        "non_milking_until",
    )

    op.drop_column(
        "animal",
        "non_milking_since",
    )

    op.drop_column(
        "animal",
        "non_milking_directive",
    )
