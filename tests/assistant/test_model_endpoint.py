"""Where the Assistant is allowed to connect, and where it is not.

AA-6 asserted the Assistant opened no socket at all. That was true only while
there was no model. The pinned runtime is llama-server reached over loopback,
so AA-7 opens a socket by design, and the boundary has to be restated as what
it always actually was: the Assistant may reach a local model and nothing else.

These tests pin that restatement. One of them starts a real HTTP server on a
loopback port and exercises the transport against it, because a permission rule
that has never been exercised against a live socket is a guess.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from dairyos_assistant.model import (
    FORBIDDEN_PORTS,
    ForbiddenEndpoint,
    LlamaServerProvider,
    ModelUnavailable,
    NullProvider,
    assert_endpoint_allowed,
)


# ---------------------------------------------------------------------------
# The permission rule
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://[::1]:8080",
        "http://127.0.0.53:11434",
    ],
)
def test_a_loopback_model_endpoint_is_permitted(url: str):
    assert_endpoint_allowed(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com:8080",
        "http://10.0.0.5:8080",
        "http://192.168.1.20:8080",
        "https://api.openai.com/v1",
        "http://dairyos.internal:8080",
    ],
)
def test_a_non_loopback_endpoint_is_refused(url: str):
    """An Assistant that can be pointed at a remote service is an Assistant
    that can be made to exfiltrate whatever it is given."""
    with pytest.raises(ForbiddenEndpoint):
        assert_endpoint_allowed(url)


@pytest.mark.parametrize("port", sorted(FORBIDDEN_PORTS))
def test_the_operational_ports_are_refused_even_on_loopback(port: int):
    """PostgreSQL and Elasticsearch both live on loopback, so being local is
    not on its own a reason to permit a connection."""
    with pytest.raises(ForbiddenEndpoint):
        assert_endpoint_allowed(f"http://127.0.0.1:{port}")


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://127.0.0.1/x", "127.0.0.1:8080"])
def test_a_non_http_endpoint_is_refused(url: str):
    with pytest.raises(ForbiddenEndpoint):
        assert_endpoint_allowed(url)


def test_a_hostname_is_refused_without_being_resolved():
    """Resolution is itself a network act, and a name that resolves to loopback
    today can resolve elsewhere tomorrow. Names are refused outright rather
    than checked."""
    with pytest.raises(ForbiddenEndpoint):
        assert_endpoint_allowed("http://localhost.attacker.example:8080")


def test_a_provider_cannot_be_constructed_pointing_somewhere_forbidden():
    """The rule is enforced in the constructor, so a misconfigured provider
    cannot exist to be called later."""
    with pytest.raises(ForbiddenEndpoint):
        LlamaServerProvider(base_url="http://203.0.113.9:8080")
    with pytest.raises(ForbiddenEndpoint):
        LlamaServerProvider(base_url="http://127.0.0.1:5432")


# ---------------------------------------------------------------------------
# The transport, against a real loopback server
# ---------------------------------------------------------------------------


class _FakeLlamaServer(BaseHTTPRequestHandler):
    content = "A withdrawal period is recorded with a start and an end time."

    def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler's interface
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        body = json.dumps({"content": self.content}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args):  # keep the test output readable
        return


@pytest.fixture
def fake_server():
    server = HTTPServer(("127.0.0.1", 0), _FakeLlamaServer)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


def test_the_provider_talks_to_a_loopback_server(fake_server: str):
    provider = LlamaServerProvider(base_url=fake_server)
    assert provider.health() is True
    assert provider.generate("explain withdrawal") == _FakeLlamaServer.content


def test_an_unreachable_model_raises_rather_than_returning_nothing():
    """A silent empty answer would be indistinguishable from a model that had
    nothing to say, and the Assistant would show it."""
    provider = LlamaServerProvider(base_url="http://127.0.0.1:1", timeout=2.0)
    with pytest.raises(ModelUnavailable):
        provider.generate("anything")


def test_no_provider_configured_raises():
    with pytest.raises(ModelUnavailable):
        NullProvider().generate("anything")


def test_the_module_depends_only_on_the_standard_library():
    """An HTTP client dependency would widen exactly the surface AA-6 narrowed."""
    import ast
    from pathlib import Path

    source = Path(__file__).resolve().parents[2] / "src" / "dairyos_assistant" / "model.py"
    imported = set()
    for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    allowed = {
        "__future__", "ipaddress", "json", "socket", "urllib", "dataclasses", "typing",
    }
    assert imported <= allowed, f"model.py gained a dependency: {sorted(imported - allowed)}"
