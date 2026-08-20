from datetime import datetime
from dairyos.data.database.session import engine
from sqlalchemy import text

today_date = datetime(2026, 8, 21).date()
print(f"=== Logging Feed & Financial Ledger Entries for {today_date} ===")

milk_volume = 593.45
milk_rate = 225.0
daily_revenue = round(milk_volume * milk_rate, 2)
daily_feed_expense = 26400.00  # 420 kg total TMR

with engine.connect() as conn:
    # 1. Clear any prior ledger entries for today
    conn.execute(
        text("DELETE FROM financial_transactions WHERE transaction_date = :d"),
        {"d": today_date}
    )

    # 2. Insert Milk Revenue & Feed Expense into Financial Ledger
    ledger_entries = [
        {
            "transaction_type": "INCOME",
            "category": "MILK_SALES",
            "amount": daily_revenue,
            "transaction_date": today_date,
            "reference": f"Daily Milk Sales: {milk_volume}L @ PKR {milk_rate}/L",
            "status": "CLEARED",
            "currency": "PKR"
        },
        {
            "transaction_type": "EXPENSE",
            "category": "FEED",
            "amount": daily_feed_expense,
            "transaction_date": today_date,
            "reference": "Daily TMR Ration: 420 kg (20 Cows)",
            "status": "CLEARED",
            "currency": "PKR"
        }
    ]

    conn.execute(
        text("""
            INSERT INTO financial_transactions (transaction_type, category, amount, transaction_date, reference, status, currency)
            VALUES (:transaction_type, :category, :amount, :transaction_date, :reference, :status, :currency)
        """),
        ledger_entries
    )
    conn.commit()

print(f"[OK] Ledger Updated:")
print(f" - Revenue: PKR {daily_revenue:,.2f}")
print(f" - Feed Expense: PKR {daily_feed_expense:,.2f}")
print(f" - Net Gross Margin: PKR {daily_revenue - daily_feed_expense:,.2f}")
print(">>> FEED & FINANCIAL TRANSACTIONS COMMITTED <<<")
