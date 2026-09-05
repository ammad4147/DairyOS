def test_notification_recipients_persist_through_settings_api(client):
    payload = {
        "recipients": [
            {
                "id": "ammad",
                "name": "Ammad Hassan",
                "designation": "",
                "email": "ammad4147@gmail.com",
            }
        ]
    }
    saved = client.put("/settings/email/recipients", json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()["recipients"][0]["email"] == "ammad4147@gmail.com"

    loaded = client.get("/settings/email/recipients")
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()["recipients"] == saved.json()["recipients"]
