"""Allow configured digest recipients without a login user.

Revision ID: 20260906_03
Revises: 20260906_02
"""
import sqlalchemy as sa
from alembic import op

revision = "20260906_03"
down_revision = "20260906_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "email_digest_deliveries",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    raise RuntimeError(
        "Configured digest-recipient delivery history cannot be safely downgraded to mandatory user identities."
    )
