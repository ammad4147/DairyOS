# -*- coding: utf-8 -*-
import csv
import os
from datetime import datetime
from dairyos.data.database.session import engine
from sqlalchemy import text

output_dir = "reports"
os.makedirs(output_dir, exist_ok=True)
timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = os.path.join(output_dir, f"financial_ledger_export_{timestamp_str}.csv")

query = """
SELECT 
    id,
    transaction_date,
    transaction_type,
    category,
    amount,
    currency,
    reference,
    status
FROM financial_transactions
ORDER BY transaction_date ASC, id ASC;
"""

print("=== EXPORTING FINANCIAL LEDGER TO CSV ===")

with engine.connect() as conn:
    result = conn.execute(text(query))
    rows = result.fetchall()
    headers = result.keys()

    with open(output_path, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(list(row))

print(f"[OK] Successfully exported {len(rows)} records.")
print(f"File Location: {os.path.abspath(output_path)}")