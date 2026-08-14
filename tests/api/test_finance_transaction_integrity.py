"""Financial ledger integrity (Phase 1, 2026-08-14).

Two defects are guarded here.

**Silent field loss.** ``POST /farm/financial`` accepted ``payment_method``,
``counterparty`` and ``notes``, returned 200, and persisted none of them
properly: only a single ``reference`` column existed, populated as
``counterparty or notes or ""``. An entry carrying both a counterparty and a
note lost the note, and payment method was never written to the ledger at
all -- which is why no report could distinguish cash from bank.

**Unclassified transaction types.** The operator UI offers six transaction
types; every report matched only the literal strings "INCOME" and "EXPENSE".
The other four were persisted, counted in ``transaction_count``, and then
contributed nothing to income, expenses or net movement. Per the farm
owner's decision (2026-08-14): RECEIPT counts as income, PAYMENT as expense,
and OWNER_WITHDRAWAL / LOAN_PAYMENT are real cash outflows that are NOT farm
expenses -- excluded from cost per litre, reported separately.
"""
from dairyos.api.reference_data import GOVERNED
from dairyos.finance.classification import transaction_classifier as classifier


def _record_financial(client, **overrides):
    payload = {
        "transaction_type": "EXPENSE",
        "amount": 1000.0,
        "category": "FEED",
        "operator": "Farm Manager",
    }
    payload.update(overrides)
    response = client.post("/farm/financial", json=payload)
    assert response.status_code == 200, response.text
    return response


def _ledger_rows():
    from dairyos.data.repositories.repository_factory import RepositoryFactory

    factory = RepositoryFactory.create()
    try:
        return list(factory.finance().get_all())
    finally:
        factory.close()


# ---------------------------------------------------------------------------
# Field persistence
# ---------------------------------------------------------------------------


def test_payment_method_reaches_the_ledger(client):
    """The concrete bug: payment_method was accepted and discarded."""
    _record_financial(
        client,
        payment_method="BANK",
        counterparty="Al-Noor Feed Mill",
        notes="Monthly silage delivery",
    )

    rows = _ledger_rows()
    assert len(rows) == 1
    assert rows[0].payment_method == "BANK"


def test_counterparty_and_notes_are_both_kept(client):
    """Previously one overwrote the other in the single `reference` column."""
    _record_financial(
        client,
        counterparty="Al-Noor Feed Mill",
        notes="Monthly silage delivery",
    )

    row = _ledger_rows()[0]
    assert row.counterparty == "Al-Noor Feed Mill"
    assert row.notes == "Monthly silage delivery"
    # `reference` keeps its previous meaning so existing readers still work.
    assert row.reference == "Al-Noor Feed Mill"


def test_unsupplied_detail_stays_null_rather_than_empty(client):
    """Absence must read as "not recorded", not as an entered blank."""
    _record_financial(client)

    row = _ledger_rows()[0]
    assert row.payment_method is None
    assert row.counterparty is None
    assert row.notes is None


def test_transaction_date_can_record_when_the_money_actually_moved(client):
    """Without this, a purchase entered late lands in the wrong period."""
    _record_financial(client, transaction_date="2026-08-01")

    row = _ledger_rows()[0]
    assert row.transaction_date.date().isoformat() == "2026-08-01"


def test_transaction_date_defaults_to_now_when_not_supplied(client):
    _record_financial(client)

    row = _ledger_rows()[0]
    assert row.transaction_date is not None


# ---------------------------------------------------------------------------
# Transaction-type classification
# ---------------------------------------------------------------------------


def test_every_advertised_transaction_type_is_classified(client):
    """No advertised type may fall through every reporting bucket."""
    for transaction_type in GOVERNED["financial_transaction_types"]:
        record = type("Row", (), {"transaction_type": transaction_type})()
        assert classifier.is_known_type(record), (
            f"{transaction_type!r} is advertised at GET /farm/reference-data "
            "but no reporting bucket claims it"
        )


def test_receipt_counts_as_income_and_payment_as_expense(client):
    _record_financial(client, transaction_type="RECEIPT", amount=500.0, category="MILK SALE")
    _record_financial(client, transaction_type="PAYMENT", amount=200.0, category="FEED")

    body = client.get("/farm/finance/reconciliation?period=yearly").json()
    assert body["income"] == 500.0
    assert body["expenses"] == 200.0
    assert body["net_movement"] == 300.0


def test_owner_withdrawal_is_not_a_farm_expense(client):
    """A drawing is a distribution of profit, not a cost of producing milk.

    Counting it as an expense would inflate cost per litre -- the number
    AA-014 exists to state honestly.
    """
    _record_financial(client, transaction_type="OWNER_WITHDRAWAL", amount=50000.0, category="DRAWINGS")

    body = client.get("/farm/finance/reconciliation?period=yearly").json()
    assert body["expenses"] == 0.0
    assert body["non_operating_outflows"] == 50000.0
    # Still visible in cash terms -- excluded from P&L, not from reality.
    assert body["net_cash_movement"] == -50000.0
    assert body["transaction_count"] == 1


def test_loan_payment_is_not_a_farm_expense(client):
    _record_financial(client, transaction_type="LOAN_PAYMENT", amount=25000.0, category="FINANCING")

    body = client.get("/farm/finance/reconciliation?period=yearly").json()
    assert body["expenses"] == 0.0
    assert body["non_operating_outflows"] == 25000.0


def test_owner_withdrawal_does_not_inflate_cost_per_litre(client, registered_animal):
    """The end-to-end consequence, stated as a number."""
    milk = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 100.0,
            "operator": "Milking Operator",
        },
    )
    assert milk.status_code == 200, milk.text

    _record_financial(client, transaction_type="EXPENSE", amount=1000.0, category="FEED")
    _record_financial(
        client, transaction_type="OWNER_WITHDRAWAL", amount=9000.0, category="DRAWINGS"
    )

    body = client.get("/farm/finance/cost-of-production?days=30").json()
    # 1000 feed / 100 litres = 10.0. Were the 9000 drawing counted, this
    # would read 100.0 -- a tenfold overstatement of the cost of milk.
    assert body["cost_per_litre"] == 10.0
    assert body["total_recorded_operating_expense"] == 1000.0
    assert body["non_operating_outflow_count"] == 1
    assert body["non_operating_outflow_total"] == 9000.0


def test_unrecognised_transaction_type_is_surfaced_not_swallowed(client):
    """An unknown type must never vanish into a total that looks complete."""
    _record_financial(client, transaction_type="SOMETHING_NEW", amount=123.0)

    body = client.get("/farm/finance/reconciliation?period=yearly").json()
    assert body["income"] == 0.0
    assert body["expenses"] == 0.0
    assert body["unclassified_transaction_count"] == 1
    assert body["unclassified_transaction_types"] == ["SOMETHING_NEW"]


# ---------------------------------------------------------------------------
# Vocabulary consistency (same guard as test_vocabulary_consistency.py)
# ---------------------------------------------------------------------------


def test_advertised_transaction_types_match_the_classifier(client):
    assert set(GOVERNED["financial_transaction_types"]) == set(classifier.KNOWN_TYPES)


def test_advertised_payment_types_are_accepted_and_persisted(client):
    """Every payment method the operator can pick must survive to the ledger."""
    for payment_method in GOVERNED["payment_types"]:
        _record_financial(client, payment_method=payment_method)

    stored = {row.payment_method for row in _ledger_rows()}
    assert stored == set(GOVERNED["payment_types"])
