"""Minimal persisted user/RBAC table (D3).

Revision ID: 20260814_03
Revises: 20260814_02

Before this migration, DairyOS had exactly one authenticatable identity: a
single env-var-configured admin login handled entirely in
``dairyos.api.auth``. Five separate "identity"/RBAC code trees existed
alongside it (application/identity, core/identity, core/models/{user,role}.py,
operations/users, platform/identity), fully wired into the application
runtime, but with zero live callers anywhere in ``api/`` -- dead weight, not
a working system, and none of them defined a persisted table.

Decision D3 (2026-08-13): delete all five dead trees and build one minimal
model instead: a single ``users`` table with governed roles (OWNER/MANAGER/
MILKER, see ``GOVERNED["auth_roles"]`` in ``dairyos.api.reference_data``),
additive to (not replacing) the existing single env-var admin login. See
``dairyos.data.models.user.User``.

This is a new table, so there is no historical data to migrate.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260814_03"
down_revision = "20260814_02"
branch_labels = None
depends_on = None


TABLE = "users"


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _existing_columns(name: str) -> set[str]:
    return {c["name"] for c in _inspector().get_columns(name)}


_EXPECTED_COLUMNS = {
    "username": sa.Column("username", sa.String(), nullable=True),
    "password_hash": sa.Column("password_hash", sa.String(), nullable=True),
    "password_salt": sa.Column("password_salt", sa.String(), nullable=True),
    "role": sa.Column("role", sa.String(), nullable=True),
    "active": sa.Column("active", sa.Boolean(), nullable=True, server_default=sa.true()),
    "created_at": sa.Column("created_at", sa.DateTime(), nullable=True),
}


def upgrade() -> None:
    if not _has_table(TABLE):
        op.create_table(
            TABLE,
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("username", sa.String(), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(), nullable=False),
            sa.Column("password_salt", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        return

    # A "users" table already existing here is NOT proof it has the right
    # shape -- "users" is a common enough name that a table can exist for
    # reasons unrelated to this migration (an earlier session's dropped-code
    # experiment, a manual create_all() run, etc). Assuming an existing
    # table already matches would silently strand the app on a schema that
    # doesn't have the columns dairyos.data.models.user.User actually reads
    # and writes -- exactly the "absence of the right shape must never
    # render as success" trap this migration exists to avoid. Instead, add
    # whatever of the expected columns are missing (nullable, since a
    # pre-existing table may already have rows with no way to backfill a
    # real password hash for them).
    existing = _existing_columns(TABLE)
    for name, column in _EXPECTED_COLUMNS.items():
        if name not in existing:
            op.add_column(TABLE, column.copy())


def downgrade() -> None:
    if not _has_table(TABLE):
        return

    op.drop_table(TABLE)
