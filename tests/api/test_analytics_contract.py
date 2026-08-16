def test_analytics_catalog_exposes_governed_backend_contract(client):
    response = client.get("/farm/analytics/catalog")

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["contract_version"] == "1.0"
    assert body["status"] == "OPERATIONAL"
    assert body["synthetic_values"] is False
    assert body["frontend_calculation_authority"] is False

    analyses = body["analyses"]

    for key in (
        "yield",
        "quality",
        "herd",
        "reproduction",
        "health",
        "feed",
        "sales",
        "thi",
    ):
        assert key in analyses
        assert analyses[key]["title"]
        assert analyses[key]["authoritative_sources"]
        assert "operational_date_basis" in analyses[key]
        assert "completeness_requirements" in analyses[key]
        assert "source_metrics" in analyses[key]


def test_analytics_catalog_does_not_claim_quality_is_implemented(client):
    response = client.get("/farm/analytics/catalog")

    assert response.status_code == 200
    assert response.json()["analyses"]["quality"]["status"] == "DEFERRED"


def test_analytics_contract_returns_single_analysis(client):
    response = client.get("/farm/analytics/yield")

    assert response.status_code == 200

    body = response.json()

    assert body["analysis"] == "yield"
    assert body["contract"]["status"] == "AVAILABLE"
    assert body["synthetic_values"] is False
    assert body["frontend_calculation_authority"] is False


def test_unknown_analytics_analysis_is_rejected(client):
    response = client.get("/farm/analytics/does-not-exist")

    assert response.status_code == 404
