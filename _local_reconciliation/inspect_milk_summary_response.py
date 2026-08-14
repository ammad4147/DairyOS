import json

from fastapi.testclient import TestClient
from dairyos.app import app

client = TestClient(app)

for period in ("7d", "30d", "3mo", "6mo", "year"):
    response = client.get(
        f"/farm/milk/production-summary?period={period}"
    )

    print(f"\n=== {period} ===")
    print("STATUS:", response.status_code)

    body = response.json()

    print(json.dumps({
        "data_status": body.get("data_status"),
        "period": body.get("period"),
        "kpis": body.get("kpis"),
        "comparison": body.get("comparison"),
        "trend": body.get("trend"),
        "production_by_animal": body.get("production_by_animal"),
        "drop_findings": body.get("drop_findings"),
        "coverage": body.get("coverage"),
        "methodology": body.get("methodology"),
    }, indent=2, default=str))
