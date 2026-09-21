"""Transport to the local model, and the refusal to talk to anything else.

The Assistant reaches ``llama-server`` over loopback HTTP. That is a socket,
and it is the only one the Assistant is permitted to open.

This module is where that permission is enforced rather than assumed. A model
endpoint is rejected unless its host is a loopback address, so a configuration
value, an environment variable or a tampered settings file cannot redirect the
Assistant at a remote service, at the operational API, or at the database. The
check happens before any connection attempt, so a forbidden endpoint never
reaches the network stack at all.

Only the standard library is used. ``urllib`` is sufficient for a local JSON
POST, and adding an HTTP client to the Assistant's dependency graph would widen
exactly the surface the packaging work spent AA-6 narrowing.
"""

from __future__ import annotations

import ipaddress
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

# Ports that must never be reached from the Assistant, whatever the host.
# PostgreSQL and the Elasticsearch index are the two routes to operational farm
# data, and a loopback address is exactly where both of them live, so being on
# localhost is not on its own a reason to allow a connection.
FORBIDDEN_PORTS = frozenset({5432, 9200})

# Model generation is optional for refusal/guidance paths: reviewed corpus
# text remains available when the local model is slow or unavailable. Keep the
# transport bounded so the operator and API do not sit behind a dead model
# server for the bridge's much longer process timeout.
DEFAULT_TIMEOUT_SECONDS = 10.0

# Generation is deliberately cold. The Assistant restates reviewed knowledge; it
# is not asked to be imaginative, and sampling variety would make its answers
# harder to test and easier to drift.
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 400


class ModelUnavailable(RuntimeError):
    """The model could not be reached. Never a reason to answer anyway."""


class ForbiddenEndpoint(ValueError):
    """The configured endpoint is one the Assistant may not open."""


_REASONING_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def strip_reasoning(text: str) -> str:
    """Remove a model's visible reasoning block.

    Thinking is disabled by request, but a model can still emit the block if a
    build ignores the flag or a template changes. Reasoning is working-out, not
    an answer: it is full of discarded candidate figures, and letting it reach
    the grounding gate would mean rejecting answers over numbers the model had
    already decided against.
    """
    return _REASONING_BLOCK.sub("", text or "").strip()


class ModelProvider(Protocol):
    def generate(self, prompt: str, *, max_tokens: int = ..., temperature: float = ...) -> str: ...


def assert_endpoint_allowed(url: str) -> None:
    """Reject any endpoint that is not a loopback model server.

    Raises before a socket is created, so a rejected endpoint produces no
    network activity whatsoever. This is the single place the Assistant's
    outbound permission is defined.
    """
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
            # A name that is not plainly loopback is refused without being
            # resolved. Resolution itself is a network act, and a hostname
            # that resolves to loopback today can resolve elsewhere tomorrow.
            raise ForbiddenEndpoint(
                f"model endpoint host must be a loopback address, got {host!r}"
            ) from exc
        if not address.is_loopback:
            raise ForbiddenEndpoint(
                f"model endpoint host must be loopback, got {host!r}"
            )

    port = parsed.port
    if port in FORBIDDEN_PORTS:
        raise ForbiddenEndpoint(
            f"port {port} is an operational data port and is never permitted"
        )


@dataclass
class LlamaServerProvider:
    """A llama.cpp ``llama-server`` reached over loopback.

    The endpoint is validated on construction, so an instance of this class
    cannot exist pointing somewhere it should not.
    """

    base_url: str = "http://127.0.0.1:8080"
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    # "chat" applies the model's own template, which is correct for an
    # instruction-tuned model. "completion" posts a raw prompt and exists only
    # for a base model or for comparing the two.
    endpoint_style: str = "chat"

    def __post_init__(self) -> None:
        assert_endpoint_allowed(self.base_url)
        if self.endpoint_style not in {"chat", "completion"}:
            raise ValueError(f"unknown endpoint_style: {self.endpoint_style!r}")

    @property
    def chat_url(self) -> str:
        return self.base_url.rstrip("/") + "/v1/chat/completions"

    @property
    def completion_url(self) -> str:
        return self.base_url.rstrip("/") + "/completion"

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        """Ask the model, through its own chat template.

        The chat endpoint is used rather than raw completion because the pinned
        model is instruction-tuned: llama-server applies the template stored in
        the GGUF, which is how the model was trained to receive instructions.
        Posting a raw string to ``/completion`` skips that and measurably
        degrades instruction-following, which for this subsystem means more
        work for the grounding gate and more withheld answers.
        """
        url = self.chat_url if self.endpoint_style == "chat" else self.completion_url
        assert_endpoint_allowed(url)

        if self.endpoint_style == "chat":
            payload: dict[str, object] = {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
                # Qwen3 reasons aloud by default. The Assistant restates
                # reviewed text; there is nothing to reason about, and the
                # thinking block would be latency spent producing tokens the
                # operator must never see.
                "chat_template_kwargs": {"enable_thinking": False},
            }
        else:
            payload = {
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": temperature,
                "cache_prompt": True,
                "stop": ["\n\nQuestion:", "\n\nOperator:", "<|im_end|>"],
            }

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ModelUnavailable(f"model server unreachable: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ModelUnavailable(f"model server returned invalid JSON: {exc}") from exc

        if self.endpoint_style == "chat":
            choices = body.get("choices") or []
            content = choices[0].get("message", {}).get("content") if choices else None
        else:
            content = body.get("content")

        if not isinstance(content, str):
            raise ModelUnavailable("model server returned no content")
        return strip_reasoning(content).strip()

    def health(self) -> bool:
        try:
            assert_endpoint_allowed(self.base_url)
            request = urllib.request.Request(
                self.base_url.rstrip("/") + "/health", method="GET"
            )
            with urllib.request.urlopen(request, timeout=5.0) as response:
                return 200 <= response.status < 300
        except Exception:  # noqa: BLE001 - health is advisory, never fatal
            return False


class NullProvider:
    """No model configured.

    Raising rather than returning an empty string is deliberate. A caller that
    forgets to check would otherwise emit a blank answer as though the model
    had produced one.
    """

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        raise ModelUnavailable("no model provider is configured")
