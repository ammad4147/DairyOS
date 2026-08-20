from dairyos.data.database.session import engine
from sqlalchemy import text

query = """
SELECT id, transaction_date, transaction_type, category, amount, currency, reference, status
FROM financial_transactions
ORDER BY transaction_date DESC, id DESC
LIMIT 10;
"""

print("=== LATEST 10 FINANCIAL TRANSACTIONS ===")
with engine.connect() as conn:
    rows = conn.execute(text(query)).fetchall()
    
    print(f"{'ID':<6} | {'Date':<10} | {'Type':<8} | {'Category':<12} | {'Amount (PKR)':<14} | {'Status':<8} | {'Reference'}")
    print("-" * 95)
    for r in rows:
        print(f"{r.id:<6} | {str(r.transaction_date):<10} | {r.transaction_type:<8} | {r.category:<12} | {r.amount:>12,.2f}  | {r.status:<8} | {r.reference}")
