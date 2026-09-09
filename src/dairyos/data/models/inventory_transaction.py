from sqlalchemy import Column, Integer, String, Float, DateTime, Index, CheckConstraint
from sqlalchemy.orm import validates
from dairyos.core.inventory_units import convert_quantity
from datetime import datetime

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class InventoryTransaction(Base):
    """One row per stock movement -- the canonical inventory ledger.

    Every operational movement is preserved with its signed quantity. Source
    metadata makes automated consumption idempotent and auditable without
    changing the operator-facing inventory model.
    """

    __tablename__ = "inventory_transactions"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    item = Column(
        String,
        nullable=False,
    )

    movement_type = Column(
        String,
        nullable=False,
    )

    quantity = Column(
        Float,
        nullable=False,
    )

    signed_quantity = Column(
        Float,
        nullable=False,
    )

    unit = Column(
        String,
        nullable=True,
    )

    location = Column(
        String,
        nullable=True,
    )

    supplier = Column(
        String,
        nullable=True,
    )

    notes = Column(
        String,
        nullable=True,
    )

    recorded_by = Column(
        String,
        nullable=True,
    )

    recorded_at = Column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    # Idempotency/audit linkage for automated movements. Nullable so all
    # historical/manual inventory rows remain valid and unchanged.
    source_type = Column(
        String,
        nullable=True,
        index=True,
    )

    source_id = Column(
        String,
        nullable=True,
        index=True,
    )

    __table_args__ = (
        CheckConstraint("quantity >= -1.7976931348623157e308 AND quantity <= 1.7976931348623157e308", name="ck_inventory_quantity_finite"),
        CheckConstraint("signed_quantity >= -1.7976931348623157e308 AND signed_quantity <= 1.7976931348623157e308", name="ck_inventory_signed_quantity_finite"),
        Index(
            "uq_inventory_transaction_source",
            "source_type",
            "source_id",
            unique=True,
        ),
    )

    @validates("quantity", "signed_quantity")
    def validate_quantity(self, key, value):
        convert_quantity(value, None, None)
        return value
