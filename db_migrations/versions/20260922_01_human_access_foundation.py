"""Add persistent human identity/session foundations for controlled access."""

from alembic import op
import sqlalchemy as sa

revision = "20260922_01"
down_revision = "20260915_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "human_identities" not in tables:
        op.create_table(
            "human_identities",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("display_name", sa.String(), nullable=False),
            sa.Column("entry_group", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("permissions_json", sa.Text(), nullable=True),
            sa.Column("pin_hash", sa.String(), nullable=True),
            sa.Column("pin_salt", sa.String(), nullable=True),
            sa.Column("pin_setup_hash", sa.String(), nullable=True),
            sa.Column("failed_pin_attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("locked_until", sa.DateTime(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_human_identities_entry_group", "human_identities", ["entry_group"])
    else:
        columns = {column["name"] for column in inspector.get_columns("human_identities")}
        if "failed_pin_attempts" not in columns:
            op.add_column("human_identities", sa.Column("failed_pin_attempts", sa.Integer(), nullable=False, server_default="0"))
        if "pin_setup_hash" not in columns:
            op.add_column("human_identities", sa.Column("pin_setup_hash", sa.String(), nullable=True))
        if "locked_until" not in columns:
            op.add_column("human_identities", sa.Column("locked_until", sa.DateTime(), nullable=True))
    if "human_sessions" not in tables:
        op.create_table(
            "human_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("session_hash", sa.String(), nullable=False),
            sa.Column("identity_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("entry_group", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_human_sessions_session_hash", "human_sessions", ["session_hash"], unique=True)
        op.create_index("ix_human_sessions_identity_id", "human_sessions", ["identity_id"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "human_sessions" in tables:
        op.drop_index("ix_human_sessions_identity_id", table_name="human_sessions")
        op.drop_index("ix_human_sessions_session_hash", table_name="human_sessions")
        op.drop_table("human_sessions")
    if "human_identities" in tables:
        columns = {column["name"] for column in inspector.get_columns("human_identities")}
        if "locked_until" in columns:
            op.drop_column("human_identities", "locked_until")
        if "failed_pin_attempts" in columns:
            op.drop_column("human_identities", "failed_pin_attempts")
        if "pin_setup_hash" in columns:
            op.drop_column("human_identities", "pin_setup_hash")
        op.drop_index("ix_human_identities_entry_group", table_name="human_identities")
        op.drop_table("human_identities")
