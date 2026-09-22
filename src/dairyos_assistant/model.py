"""Transport to the local model, and the refusal to talk to anything else.

The Assistant reaches ``llama-server`` over loopback HTTP. That socket is the
only one it may open. An endpoint is rejected unless its host is loopback and
its port is not an operational data port, before any connection is attempted.

Timeouts are separated because they fail for different reasons and deserve
different limits:

``connect``      the server is not listening (seconds)
``first_token``  the server accepted the request but prompt processing has not
                 produced a token (covers prompt evaluation on slow CPUs)
``stall``        tokens stopped arriving mid-answer (a hung worker)
``total``        the whole answer took too long to be useful to an operator

Generation streams (server-sent events), so time-to-first-token and tokens per
second are measured on every call and reported in diagnostics. The limits come
from a runtime profile chosen by the DairyOS bridge from measured hardware, not
from a fixed constant.

Only the standard library is used.
"""

from __future__ import annotations

import http.client
import ipaddress
import json
import re
import time
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse

# Ports that must never be reached from the Assistant, whatever the host.
# PostgreSQL and the Elasticsearch index are the two routes to operational farm data.
FORBIDDEN_PORTS = frozenset({5432, 9200})

DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 380


@dataclass(frozen=True)
class Timeouts:
    connect: float = 3.0
    first_token: float = 45.0
    stall: float = 20.0
    total: float = 120.0

    @classmethod
    def from_mapping(cls, values: dict | None) -> Timeouts:
        values = values or {}
        return cls(**{k: float(v) for k, v in values.items() if k in {"connect", "first_token", "stall", "total"}})


class ModelUnavailable(RuntimeError):
    """The model could not be reached or did not answer in time. Never a reason to answer anyway."""

    def __init__(self, message: str, kind: str = "unavailable"):
        super().__init__(message)
        self.kind = kind


class ForbiddenEndpoint(ValueError):
    """The configured endpoint is one the Assistant may not open."""


@dataclass
class Generation:
    text: str
    ttft_s: float | None = None
    total_s: float = 0.0
    tokens: int = 0
    tokens_per_s: float | None = None
    prompt_tokens: int | None = None
    prompt_ms: float | None = None
    finish_reason: str | None = None
    timings: dict = field(default_factory=dict)


_REASONING_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def strip_reasoning(text: str) -> str:
    """Remove a model's visible reasoning block; it is working-out, not an answer."""
    return _REASONING_BLOCK.sub("", text or "").replace("<think>", "").replace("</think>", "").strip()


class ModelProvider(Protocol):
    def generate(self, prompt: str, *, system: str | None = ..., max_tokens: int = ..., temperature: float = ...) -> Generation: ...


def assert_endpoint_allowed(url: str) -> None:
    """Reject any endpoint that is not a loopback model server, before any socket exists."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ForbiddenEndpoint(f"model endpoint must be http or https, got {parsed.scheme!r}")
    host = parsed.hostname
    if not host:
        raise ForbiddenEndpoint(f"model endpoint has no host: {url!r}")
    if host not in {"localhost", "localhost.localdomain"}:
        try:
            address = ipaddress.ip_address(host)
        except ValueError as exc:
            raise ForbiddenEndpoint(f"model endpoint host must be a loopback address, got {host!r}") from exc
        if not address.is_loopback:
            raise ForbiddenEndpoint(f"model endpoint host must be loopback, got {host!r}")
    if parsed.port in FORBIDDEN_PORTS:
        raise ForbiddenEndpoint(f"port {parsed.port} is an operational data port and is never permitted")


@dataclass
class LlamaServerProvider:
    """A llama.cpp ``llama-server`` reached over loopback with streamed chat completions."""

    base_url: str = "http://127.0.0.1:8080"
    timeouts: Timeouts = field(default_factory=Timeouts)
    # Backwards-compatible single timeout; when given it bounds every phase.
    timeout: float | None = None

    def __post_init__(self) -> None:
        assert_endpoint_allowed(self.base_url)
        if self.timeout is not None:
            t = float(self.timeout)
            self.timeouts = Timeouts(connect=min(3.0, t), first_token=t, stall=t, total=t)
        parsed = urlparse(self.base_url)
        self._host = parsed.hostname or "127.0.0.1"
        self._port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self._https = parsed.scheme == "https"

    def _connection(self) -> http.client.HTTPConnection:
        cls = http.client.HTTPSConnection if self._https else http.client.HTTPConnection
        return cls(self._host, self._port, timeout=self.timeouts.connect)

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> Generation:
        assert_endpoint_allowed(self.base_url)
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "cache_prompt": True,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        started = time.perf_counter()
        connection = self._connection()
        try:
            try:
                connection.connect()
            except OSError as exc:
                raise ModelUnavailable(f"model server not reachable: {exc}", "connect") from exc
            # Keep our own reference: http.client may drop connection.sock once the
            # response is marked to close, but the socket stays live for reading.
            sock = connection.sock
            sock.settimeout(self.timeouts.first_token)
            body = json.dumps(payload).encode("utf-8")
            connection.request("POST", "/v1/chat/completions", body=body, headers={"Content-Type": "application/json"})
            try:
                response = connection.getresponse()
            except TimeoutError as exc:
                raise ModelUnavailable("model did not start answering in time", "first_token") from exc
            except OSError as exc:
                raise ModelUnavailable(f"model server error: {exc}", "connect") from exc
            if response.status != 200:
                raise ModelUnavailable(f"model server returned HTTP {response.status}", "http")
            pieces: list[str] = []
            first_token_at: float | None = None
            finish_reason = None
            timings: dict = {}
            usage: dict = {}
            while True:
                if time.perf_counter() - started > self.timeouts.total:
                    raise ModelUnavailable("model answer exceeded the total time limit", "total")
                try:
                    raw = response.readline()
                except TimeoutError as exc:
                    kind = "first_token" if first_token_at is None else "stall"
                    raise ModelUnavailable(f"model stopped responding ({kind})", kind) from exc
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = event.get("choices") or []
                if choices:
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if content:
                        if first_token_at is None:
                            first_token_at = time.perf_counter()
                            sock.settimeout(self.timeouts.stall)
                        pieces.append(content)
                    finish_reason = choices[0].get("finish_reason") or finish_reason
                timings = event.get("timings") or timings
                usage = event.get("usage") or usage
        except TimeoutError as exc:
            raise ModelUnavailable("model timed out", "stall") from exc
        finally:
            connection.close()
        total = time.perf_counter() - started
        text = strip_reasoning("".join(pieces)).strip()
        if not text:
            raise ModelUnavailable("model returned no content", "empty")
        predicted = timings.get("predicted_n") or usage.get("completion_tokens") or len(pieces)
        tps = timings.get("predicted_per_second")
        if tps is None and first_token_at is not None and total > (first_token_at - started):
            tps = predicted / max(total - (first_token_at - started), 1e-6)
        return Generation(
            text=text,
            ttft_s=round(first_token_at - started, 3) if first_token_at else None,
            total_s=round(total, 3),
            tokens=int(predicted or 0),
            tokens_per_s=round(float(tps), 2) if tps else None,
            prompt_tokens=timings.get("prompt_n") or usage.get("prompt_tokens"),
            prompt_ms=timings.get("prompt_ms"),
            finish_reason=finish_reason,
            timings=timings,
        )

    def health(self) -> bool:
        try:
            connection = http.client.HTTPConnection(self._host, self._port, timeout=min(2.0, self.timeouts.connect))
            connection.request("GET", "/health")
            ok = 200 <= connection.getresponse().status < 300
            connection.close()
            return ok
        except Exception:  # noqa: BLE001 - health is advisory, never fatal
            return False


class NullProvider:
    """No model configured. Raising, rather than returning '', keeps callers honest."""

    def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = DEFAULT_MAX_TOKENS,
                 temperature: float = DEFAULT_TEMPERATURE) -> Generation:
        raise ModelUnavailable("no model provider is configured", "none")

    def health(self) -> bool:
        return False
