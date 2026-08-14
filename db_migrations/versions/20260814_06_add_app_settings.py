"""Application settings key/value table (AA-013 §17; farm identity, reset protection).

Revision ID: 20260814_06
Revises: 20260814_05

See `src/dairyos/data/models/app_setting.py` for the full design rationale.

Follows the self-healing column-repair pattern established on 20260814_03
and reused on 20260814_04/20260814_05: a table name existing is never
treated as proof it already has the right shape.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260814_06"
down_revision = "20260814_05"
branch_labels = None
depends_on = None


SETTINGS_TABLE = "app_settings"


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _existing_columns(name: str) -> set[str]:
    return {c["name"] for c in _inspector().get_columns(name)}


_EXPECTED_COLUMNS = {
    "value": sa.Column("value", sa.String(), nullable=True),
    "updated_at": sa.Column("updated_at", sa.DateTime(), nullable=True),
    "updated_by": sa.Column("updated_by", sa.String(), nullable=True),
}


def upgrade() -> None:
    if not _has_table(SETTINGS_TABLE):
        op.create_table(
            SETTINGS_TABLE,
            sa.Column("key", sa.String(), primary_key=True),
            sa.Column("value", sa.String(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("updated_by", sa.String(), nullable=True),
        )
    else:
        existing = _existing_columns(SETTINGS_TABLE)
        for name, column in _EXPECTED_COLUMNS.items():
            if name not in existing:
                op.add_column(SETTINGS_TABLE, column.copy())


def downgrade() -> None:
    if _has_table(SETTINGS_TABLE):
        op.drop_table(SETTINGS_TABLE)
