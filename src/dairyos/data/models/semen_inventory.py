from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from dairyos.core.time_utils import utcnow
from dairyos.data.database.base import Base


class SemenLot(Base):
    __tablename__ = "semen_lots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lot_code = Column(String, nullable=False, unique=True, index=True)
    sire_code = Column(String, nullable=False, index=True)
    bull_name = Column(String, nullable=True)
    breed = Column(String, nullable=True)
    semen_type = Column(String, nullable=False, index=True)
    supplier = Column(String, nullable=False, index=True)
    batch_number = Column(String, nullable=False, index=True)
    purchase_transaction_id = Column(Integer, ForeignKey("financial_transactions.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    purchase_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    storage_location = Column(String, nullable=True)
    country_source = Column(String, nullable=True)
    unit_cost = Column(Numeric(18, 6), nullable=False)
    purchased_quantity = Column(Integer, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class SemenStockMovement(Base):
    __tablename__ = "semen_stock_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    semen_lot_id = Column(Integer, ForeignKey("semen_lots.id", ondelete="RESTRICT"), nullable=False, index=True)
    movement_type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    signed_quantity = Column(Integer, nullable=False)
    source_financial_transaction_id = Column(Integer, ForeignKey("financial_transactions.id", ondelete="RESTRICT"), nullable=True, index=True)
    breeding_record_id = Column(String, nullable=True, unique=True, index=True)
    notes = Column(Text, nullable=True)
    recorded_by = Column(String, nullable=True)
    recorded_at = Column(DateTime, nullable=False, default=utcnow)
