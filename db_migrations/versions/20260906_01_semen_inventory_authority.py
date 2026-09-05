"""Add governed semen lot inventory and breeding provenance.

Revision ID: 20260906_01
Revises: 20260905_04
"""
import sqlalchemy as sa
from alembic import op

revision = "20260906_01"
down_revision = "20260905_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "semen_lots" not in tables:
        op.create_table(
            "semen_lots",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("lot_code", sa.String(), nullable=False),
            sa.Column("sire_code", sa.String(), nullable=False),
            sa.Column("bull_name", sa.String(), nullable=True),
            sa.Column("breed", sa.String(), nullable=True),
            sa.Column("semen_type", sa.String(), nullable=False),
            sa.Column("supplier", sa.String(), nullable=False),
            sa.Column("batch_number", sa.String(), nullable=False),
            sa.Column("purchase_transaction_id", sa.Integer(), sa.ForeignKey("financial_transactions.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("purchase_date", sa.Date(), nullable=False),
            sa.Column("expiry_date", sa.Date(), nullable=True),
            sa.Column("storage_location", sa.String(), nullable=True),
            sa.Column("country_source", sa.String(), nullable=True),
            sa.Column("unit_cost", sa.Numeric(18, 6), nullable=False),
            sa.Column("purchased_quantity", sa.Integer(), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("lot_code", name="uq_semen_lots_lot_code"),
            sa.UniqueConstraint("purchase_transaction_id", name="uq_semen_lots_purchase_transaction_id"),
        )
        for name, cols in (
            ("ix_semen_lots_lot_code", ["lot_code"]),
            ("ix_semen_lots_sire_code", ["sire_code"]),
            ("ix_semen_lots_semen_type", ["semen_type"]),
            ("ix_semen_lots_supplier", ["supplier"]),
            ("ix_semen_lots_batch_number", ["batch_number"]),
        ):
            op.create_index(name, "semen_lots", cols)

    if "semen_stock_movements" not in tables:
        op.create_table(
            "semen_stock_movements",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("semen_lot_id", sa.Integer(), sa.ForeignKey("semen_lots.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("movement_type", sa.String(), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("signed_quantity", sa.Integer(), nullable=False),
            sa.Column("source_financial_transaction_id", sa.Integer(), sa.ForeignKey("financial_transactions.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("breeding_record_id", sa.String(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("recorded_by", sa.String(), nullable=True),
            sa.Column("recorded_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("breeding_record_id", name="uq_semen_stock_movements_breeding_record_id"),
        )
        op.create_index("ix_semen_stock_movements_lot", "semen_stock_movements", ["semen_lot_id"])
        op.create_index("ix_semen_stock_movements_finance", "semen_stock_movements", ["source_financial_transaction_id"])

    columns = {c["name"] for c in sa.inspect(bind).get_columns("breeding_records")}
    if "semen_lot_id" not in columns:
        op.add_column("breeding_records", sa.Column("semen_lot_id", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_breeding_records_semen_lot", "breeding_records", "semen_lots", ["semen_lot_id"], ["id"], ondelete="RESTRICT")
    if "semen_supplier" not in columns:
        op.add_column("breeding_records", sa.Column("semen_supplier", sa.String(), nullable=True))
    if "semen_batch_number" not in columns:
        op.add_column("breeding_records", sa.Column("semen_batch_number", sa.String(), nullable=True))
    if "semen_unit_cost" not in columns:
        op.add_column("breeding_records", sa.Column("semen_unit_cost", sa.Numeric(18, 6), nullable=True))


def downgrade() -> None:
    raise RuntimeError("Semen provenance and stock history are operational audit records and cannot be destructively downgraded.")
