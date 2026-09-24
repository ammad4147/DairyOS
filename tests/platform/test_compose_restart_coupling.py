from pathlib import Path

import yaml


def test_api_restarts_when_compose_restarts_or_recreates_database():
    compose_file = Path(__file__).resolve().parents[2] / "docker-compose.yml"
    compose = yaml.safe_load(compose_file.read_text(encoding="utf-8"))

    assert compose["services"]["api"]["depends_on"]["db"] == {
        "condition": "service_healthy",
        "restart": True,
    }
