from sqlalchemy import text

from dairyos.api.dependencies import get_container


def test_health(client):

    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "healthy"


def test_system_health_is_current_read_only_integrity_report(client):
    session = get_container().repository_factory.session
    before = {
        table: int(
            session.execute(text(f'SELECT count(*) FROM "{table}"')).scalar_one()
        )
        for table in ("app_settings", "event_journal", "health_observation")
    }

    response = client.get("/farm/system-health")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["health_schema_version"] == 2
    assert payload["read_only"] is True
    assert payload["data_status"] == "LIVE_PERSISTED_DATA_READ_ONLY"
    assert payload["checked_at"].endswith("Z")
    assert payload["overall"] in {"PASS", "WARNING"}
    assert {check["name"] for check in payload["checks"]} >= {
        "database",
        "schema",
        "schema columns",
        "health observation persistence",
        "event projections",
        "health observation animal links",
        "health observation case links",
        "backup protection",
        "data layout",
        "AI Assistant knowledge",
        "application runtime",
    }
    assert all(check["status"] in {"PASS", "WARNING", "FAIL"} for check in payload["checks"])

    after = {
        table: int(
            session.execute(text(f'SELECT count(*) FROM "{table}"')).scalar_one()
        )
        for table in before
    }
    assert after == before
