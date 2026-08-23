from fastapi.testclient import TestClient


def test_react_preflight_is_allowed(client: TestClient):
    response = client.options(
        "/authz/permissions",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    assert response.headers.get("access-control-allow-methods")
    assert "authorization" in response.headers.get("access-control-allow-headers", "").lower()
    assert "content-type" in response.headers.get("access-control-allow-headers", "").lower()
