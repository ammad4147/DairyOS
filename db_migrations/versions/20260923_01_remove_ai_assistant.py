"""Remove AI Assistant persistence after subsystem eradication.

The historical Assistant migration remains in the Alembic chain so older
DairyOS databases can still be upgraded. Current DairyOS permanently retires
the Assistant persistence objects.

Real installations may contain partially retired Assistant schema state.
Removal is therefore intentionally idempotent for these retired objects.
"""

from alembic import op

revision = "20260923_01"
down_revision = "20260922_01"
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL automatically removes table-owned indexes when the table is
    # dropped. RESTRICT semantics are intentional: unexpected external
    # dependencies must block retirement rather than be cascade-deleted.
    op.execute("DROP TABLE IF EXISTS ai_assistant_messages")
    op.execute("DROP TABLE IF EXISTS ai_assistant_conversations")


def downgrade():
    raise RuntimeError(
        "The AI Assistant has been permanently removed from DairyOS. "
        "Restore a verified compatible backup with an earlier DairyOS version instead."
    )
