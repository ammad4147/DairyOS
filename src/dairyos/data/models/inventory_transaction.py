from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class InventoryTransaction(Base):
    """One row per stock movement -- the canonical ledger (G8.1, 2026-08-14).

    Before this model existed, `POST /farm/inventory` was event-journal-only:
    no queryable stock model, no balance, nothing an operator could ask
    "how much feed do we have left" against. Decision (build-spec Session 8,
    reconfirmed via AskUserQuestion 2026-08-14): stock is derived by summing
    signed movements, never stored as a separately-maintained running total
    that could drift from its own history.

    Direction of each of the six real movement types the operator UI offers
    (PURCHASE/RECEIPT/CONSUMPTION/TRANSFER/WASTAGE/ADJUSTMENT):

    - PURCHASE, RECEIPT: always increase stock. `quantity` must be entered
      positive; `signed_quantity` is `+quantity`.
    - CONSUMPTION, WASTAGE: always decrease stock. `quantity` must be
      entered positive; `signed_quantity` is `-quantity`.
    - TRANSFER, ADJUSTMENT: direction isn't implied by the type name alone
      (a transfer can be inbound or outbound; an adjustment can correct
      stock up or down), so the operator enters a signed `quantity`
      directly and `signed_quantity` equals it unchanged.

    `quantity` is kept as exactly what was submitted (audit fidelity -- what
    did the operator actually type); `signed_quantity` is the value balance
    queries sum, so a balance calculation never has to re-derive sign from
    movement_type and risk disagreeing with what validation already
    enforced at write time.
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
