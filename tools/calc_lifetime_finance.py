# -*- coding: utf-8 -*-
from dairyos.data.database.session import engine
from sqlalchemy import text

query = """
SELECT 
    transaction_type,
    category,
    COUNT(*) as total_count,
    SUM(amount) as total_amount
FROM financial_transactions
GROUP BY transaction_type, category
ORDER BY transaction_type, category;
"""

overall_query = """
SELECT 
    COALESCE(SUM(CASE WHEN transaction_type = 'INCOME' THEN amount ELSE 0 END), 0) as total_income,
    COALESCE(SUM(CASE WHEN transaction_type = 'EXPENSE' THEN amount ELSE 0 END), 0) as total_expense,
    COUNT(*) as total_transactions,
    MIN(transaction_date) as start_date,
    MAX(transaction_date) as end_date
FROM financial_transactions;
"""

print("=== LIFETIME FINANCIAL LEDGER SUMMARY ===")
with engine.connect() as conn:
    overall = conn.execute(text(overall_query)).fetchone()
    breakdown = conn.execute(text(query)).fetchall()
    
    total_income = float(overall.total_income)
    total_expense = float(overall.total_expense)
    net_margin = total_income - total_expense
    margin_pct = (net_margin / total_income * 100) if total_income > 0 else 0.0

    print(f"Ledger Timeline:        {overall.start_date} to {overall.end_date}")
    print(f"Total Transactions:     {overall.total_transactions}")
    print("-" * 65)
    print(f"Total Lifetime Revenue:  PKR {total_income:>15,.2f}")
    print(f"Total Lifetime Expenses: PKR {total_expense:>15,.2f}")
    print(f"Cumulative Net Margin:   PKR {net_margin:>15,.2f} ({margin_pct:.1f}%)")
    print("-" * 65)
    print("\nDetailed Category Breakdown:")
    for b in breakdown:
        print(f" - [{b.transaction_type:<7}] {b.category:<14}: PKR {float(b.total_amount):>14,.2f} ({b.total_count} tx)")