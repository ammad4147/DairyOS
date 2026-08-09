def test_dashboard_preserves_legacy_payload_and_exposes_view(client):
    response = client.get("/dashboard")

    assert response.status_code == 200

    body = response.json()

    assert "dashboard" in body
    assert "milk" in body["dashboard"]

    milk_zone = next(
        zone
        for zone in body["dashboard_view"]["layout"]["zones"]
        if zone["zone_id"] == "milk"
    )

    assert {widget["widget_id"] for widget in milk_zone["widgets"]} == {
        "milk.today",
        "milk.shift",
        "milk.operator",
    }
