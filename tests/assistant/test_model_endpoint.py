"""The model transport: loopback-only, streamed, with separate timeouts."""

from __future__ import annotations

import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from dairyos_assistant.model import (
    ForbiddenEndpoint,
    LlamaServerProvider,
    ModelUnavailable,
    NullProvider,
    Timeouts,
    assert_endpoint_allowed,
    strip_reasoning,
)


@pytest.mark.parametrize("url", ["http://127.0.0.1:8080", "http://localhost:9000", "http://[::1]:8080"])
def test_a_loopback_model_endpoint_is_permitted(url: str):
    assert_endpoint_allowed(url)


@pytest.mark.parametrize("url", ["http://10.0.0.5:8080", "http://192.168.1.2:8080", "http://8.8.8.8"])
def test_a_non_loopback_endpoint_is_refused(url: str):
    with pytest.raises(ForbiddenEndpoint):
        assert_endpoint_allowed(url)


@pytest.mark.parametrize("port", [5432, 9200])
def test_the_operational_ports_are_refused_even_on_loopback(port: int):
    with pytest.raises(ForbiddenEndpoint):
        assert_endpoint_allowed(f"http://127.0.0.1:{port}")


@pytest.mark.parametrize("url", ["ftp://127.0.0.1", "file:///etc/passwd", "postgresql://127.0.0.1:5432/dairyos"])
def test_a_non_http_endpoint_is_refused(url: str):
    with pytest.raises(ForbiddenEndpoint):
        assert_endpoint_allowed(url)


def test_a_hostname_is_refused_without_being_resolved():
    with pytest.raises(ForbiddenEndpoint):
        assert_endpoint_allowed("http://model.example.com:8080")


def test_a_provider_cannot_be_constructed_pointing_somewhere_forbidden():
    with pytest.raises(ForbiddenEndpoint):
        LlamaServerProvider(base_url="http://10.1.1.1:8080")


class _Server:
    """A fake llama-server that streams server-sent events with controllable delays."""

    def __init__(self, *, first_delay: float = 0.0, gap: float = 0.0, chunks=("Hello", " there.")):
        self.first_delay, self.gap, self.chunks = first_delay, gap, list(chunks)
        self.requests: list[dict] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # noqa: D401 - silence
                pass

            def do_GET(self):  # health
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')

            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                outer.requests.append(json.loads(self.rfile.read(length)))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                time.sleep(outer.first_delay)
                try:
                    for i, chunk in enumerate(outer.chunks):
                        if i:
                            time.sleep(outer.gap)
                        event = {"choices": [{"delta": {"content": chunk}, "finish_reason": None}]}
                        self.wfile.write(f"data: {json.dumps(event)}\n\n".encode())
                        self.wfile.flush()
                    final = {"choices": [{"delta": {}, "finish_reason": "stop"}],
                             "timings": {"predicted_n": len(outer.chunks), "predicted_per_second": 42.0, "prompt_n": 100}}
                    self.wfile.write(f"data: {json.dumps(final)}\n\ndata: [DONE]\n\n".encode())
                except (BrokenPipeError, ConnectionResetError):
                    pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


@pytest.fixture
def server():
    created = []

    def make(**kwargs):
        s = _Server(**kwargs)
        created.append(s)
        return s

    yield make
    for s in created:
        s.close()


def test_generation_streams_and_measures_first_token(server):
    s = server(chunks=("The answer", " is here."))
    result = LlamaServerProvider(base_url=s.url).generate("q", system="sys")
    assert result.text == "The answer is here."
    assert result.ttft_s is not None and result.tokens_per_s == 42.0
    request = s.requests[0]
    assert request["stream"] is True
    assert request["messages"][0] == {"role": "system", "content": "sys"}
    assert request["chat_template_kwargs"] == {"enable_thinking": False}


def test_slow_prompt_processing_is_a_first_token_timeout(server):
    s = server(first_delay=1.5)
    provider = LlamaServerProvider(base_url=s.url, timeouts=Timeouts(connect=1, first_token=0.5, stall=5, total=10))
    with pytest.raises(ModelUnavailable) as excinfo:
        provider.generate("q")
    assert excinfo.value.kind == "first_token"


def test_a_stalled_stream_is_a_stall_timeout(server):
    s = server(gap=1.5, chunks=("a", "b"))
    provider = LlamaServerProvider(base_url=s.url, timeouts=Timeouts(connect=1, first_token=5, stall=0.5, total=10))
    with pytest.raises(ModelUnavailable) as excinfo:
        provider.generate("q")
    assert excinfo.value.kind == "stall"


def test_a_long_answer_hits_the_total_limit(server):
    s = server(gap=0.3, chunks=tuple("abcdefgh"))
    provider = LlamaServerProvider(base_url=s.url, timeouts=Timeouts(connect=1, first_token=5, stall=5, total=1.0))
    with pytest.raises(ModelUnavailable) as excinfo:
        provider.generate("q")
    assert excinfo.value.kind == "total"


def test_a_slow_but_steady_answer_is_not_cut_off(server):
    """The old 10 s single deadline cut off answers that were progressing; streaming limits do not."""
    s = server(first_delay=0.4, gap=0.2, chunks=("one", " two", " three"))
    provider = LlamaServerProvider(base_url=s.url, timeouts=Timeouts(connect=1, first_token=2, stall=1, total=10))
    assert provider.generate("q").text == "one two three"


def test_an_unreachable_model_is_a_connect_failure():
    provider = LlamaServerProvider(base_url="http://127.0.0.1:1", timeouts=Timeouts(connect=0.5))
    with pytest.raises(ModelUnavailable) as excinfo:
        provider.generate("q")
    assert excinfo.value.kind == "connect"
    assert provider.health() is False


def test_no_provider_configured_raises():
    with pytest.raises(ModelUnavailable):
        NullProvider().generate("q")


@pytest.mark.parametrize(
    "raw,expected",
    [("<think>reasoning 42</think>Answer.", "Answer."), ("Plain answer.", "Plain answer."), ("<think></think>\nA", "A")],
)
def test_a_reasoning_block_is_stripped(raw: str, expected: str):
    assert strip_reasoning(raw) == expected


def test_the_module_depends_only_on_the_standard_library():
    import ast

    source = Path(sys.modules[LlamaServerProvider.__module__].__file__).read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    allowed = {"__future__", "http", "ipaddress", "json", "re", "time", "dataclasses", "typing", "urllib"}
    assert imported <= allowed, f"model.py gained a dependency: {sorted(imported - allowed)}"
