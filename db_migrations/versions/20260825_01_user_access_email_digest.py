"""Expand user access control and add nightly email digest persistence.

Revision ID: 20260825_01
Revises: 20260817_02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260825_01"
down_revision = "20260817_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    user_columns = {c["name"] for c in inspector.get_columns("users")}
    if "personal_email" not in user_columns:
        op.add_column("users", sa.Column("personal_email", sa.String(), nullable=True))
    if "job_title" not in user_columns:
        op.add_column("users", sa.Column("job_title", sa.String(), nullable=True))
    if "permissions_json" not in user_columns:
        op.add_column("users", sa.Column("permissions_json", sa.Text(), nullable=True))

    tables = set(inspector.get_table_names())
    if "email_sender_settings" not in tables:
        op.create_table(
            "email_sender_settings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("sender_email", sa.String(), nullable=False),
            sa.Column("sender_display_name", sa.String(), nullable=True),
            sa.Column("smtp_host", sa.String(), nullable=True),
            sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="587"),
            sa.Column("smtp_username", sa.String(), nullable=True),
            sa.Column("smtp_password_ciphertext", sa.Text(), nullable=True),
            sa.Column("use_tls", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("updated_by", sa.String(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if "email_digest_runs" not in tables:
        op.create_table(
            "email_digest_runs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("digest_date", sa.Date(), nullable=False, unique=True),
            sa.Column("scheduled_at", sa.DateTime(), nullable=False),
            sa.Column("generated_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    if "email_digest_deliveries" not in tables:
        op.create_table(
            "email_digest_deliveries",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("digest_run_id", sa.Integer(), sa.ForeignKey("email_digest_runs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("recipient_email", sa.String(), nullable=False),
            sa.Column("sent_at", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index(
            "ix_email_digest_deliveries_run_user",
            "email_digest_deliveries",
            ["digest_run_id", "user_id"],
            unique=True,
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "email_digest_deliveries" in tables:
        op.drop_index("ix_email_digest_deliveries_run_user", table_name="email_digest_deliveries")
        op.drop_table("email_digest_deliveries")
    if "email_digest_runs" in tables:
        op.drop_table("email_digest_runs")
    if "email_sender_settings" in tables:
        op.drop_table("email_sender_settings")

    user_columns = {c["name"] for c in inspector.get_columns("users")}
    if "permissions_json" in user_columns:
        op.drop_column("users", "permissions_json")
    if "job_title" in user_columns:
        op.drop_column("users", "job_title")
    if "personal_email" in user_columns:
        op.drop_column("users", "personal_email")
