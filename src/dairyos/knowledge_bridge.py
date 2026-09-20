"""Supervision of the Assistant process, from the operational side.

DairyOS starts two child processes for the Assistant: the llama.cpp model
server, and the Assistant itself. This module owns both lifetimes so that
closing DairyOS leaves nothing running.

**The environment is the boundary.** The Assistant child is started with every
``DAIRYOS_*`` variable and every PostgreSQL variable removed from its
environment. That is not decoration: the operational configuration builds a
database URL from exactly those variables and falls back to a passwordless
loopback default when they are absent, so withholding them is what makes the
database unreachable rather than merely unused. The Assistant's own package
cannot import a driver either, and the frozen build excludes one, but each of
those is a separate layer and this is the one that lives here.

Nothing in this module imports the Assistant package. The two sides speak JSON
lines over a pipe and share no code, which is what keeps the isolation argument
true of the running system rather than only of the source tree.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Variables that would give the child a route to operational state, or the
# credentials to unlock one. Removed from its environment without exception.
STRIPPED_PREFIXES = ("DAIRYOS_",)
STRIPPED_NAMES = frozenset({
    "PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE", "PGSERVICE",
    "DATABASE_URL", "ELASTICSEARCH_URL",
})

MODEL_PORT = 8477
MODEL_READY_TIMEOUT = 180.0
# How long the first question of a session will wait for the model to
# finish loading before being answered from approved knowledge instead.
MODEL_FIRST_USE_WAIT = 180.0
REQUEST_TIMEOUT = 90.0

# Kept deliberately small. A question that has not been answered in this long
# has failed, and an operator staring at a spinner is worse served than one
# told to try again.
ASSISTANT_START_TIMEOUT = 60.0


class _Timeout(Exception):
    """The child did not answer in time."""


def _read_line(child: subprocess.Popen, timeout: float) -> str:
    """One line from the child, or give up.

    ``readline`` on a pipe blocks indefinitely and cannot be interrupted, so
    the read happens on a throwaway thread that the caller can abandon. The
    thread leaks if the child never writes, which is why the caller kills the
    child: a dead child closes the pipe and the thread ends.
    """
    result: list[str] = []

    def reader() -> None:
        try:
            result.append(child.stdout.readline())
        except Exception:  # noqa: BLE001 - reported as a timeout by the caller
            pass

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive() or not result:
        raise _Timeout()
    return result[0]


def sanitised_environment() -> dict[str, str]:
    """The environment the Assistant child is allowed to see."""
    clean = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(STRIPPED_PREFIXES) and key not in STRIPPED_NAMES
    }
    # The child needs to find its own package when running from source. In a
    # frozen build it is its own executable and this is ignored.
    clean.setdefault("PYTHONUNBUFFERED", "1")
    return clean


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _assistant_roots() -> list[Path]:
    """Return approved Core/source and separately managed Assistant roots."""
    roots = []
    configured = os.environ.get("DAIRYOS_ASSISTANT_ROOT", "").strip()
    if configured:
        roots.append(Path(configured))
    if os.name == "nt":
        roots.append(Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "DairyOS" / "assistant")
    roots.append(_bundle_root() / "assistant")
    roots.append(_bundle_root())
    return roots


def assistant_command() -> list[str] | None:
    """How to start the Assistant, frozen or from source."""
    executable = "DairyOSAssistant.exe" if os.name == "nt" else "DairyOSAssistant"
    for root in _assistant_roots():
        frozen = root / executable
        if frozen.is_file():
            return [str(frozen)]
    if getattr(sys, "frozen", False):
        # A frozen DairyOS whose Assistant executable is absent. The build
        # refuses to produce this, so it means a tampered or partial install.
        return None
    service = root / "src" / "dairyos_assistant" / "service.py"
    if service.is_file():
        return [sys.executable, str(service)]
    return None


def model_paths() -> tuple[Path, Path] | None:
    """The bundled model and server, wherever this build keeps them."""
    candidates = []
    for root in _assistant_roots():
        candidates.extend(
            [
                (root / "_internal" / "assistant-runtime", root / "_internal" / "assistant-runtime"),
                (root / "assistant-runtime", root / "assistant-runtime"),
                (root / "runtime" / "assistant", root / "runtime" / "assistant"),
            ]
        )
    server_name = "llama-server.exe" if os.name == "nt" else "llama-server"
    for base, _ in candidates:
        model = next(iter(sorted((base / "model").glob("*.gguf"))), None) if (base / "model").is_dir() else None
        server = base / "llama" / server_name
        if model and server.is_file():
            return model, server
    return None


@dataclass
class AssistantBridge:
    """Starts, questions and stops the Assistant. One instance per process."""

    model_port: int = MODEL_PORT
    _model: subprocess.Popen | None = None
    _child: subprocess.Popen | None = None
    # default_factory, not a bare default: a dataclass evaluates a plain
    # default once at class-definition time, so every bridge shared one
    # lock and a blocked instance could stall the singleton.
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _model_awaited: bool = False
    _last_error: str = ""

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> bool:
        with self._lock:
            if self._child is not None and self._child.poll() is None:
                return True
            return self._start_locked()

    def _start_locked(self) -> bool:
        runtime = model_paths()
        command = assistant_command()
        if command is None:
            self._last_error = "the Assistant executable is not present in this installation"
            logger.warning("Assistant not started: %s", self._last_error)
            return False

        environment = sanitised_environment()
        model_url = ""
        if runtime is not None:
            model, server = runtime
            if self._model is None or self._model.poll() is not None:
                self._model = subprocess.Popen(
                    [
                        str(server), "-m", str(model),
                        "--host", "127.0.0.1", "--port", str(self.model_port),
                        "-c", "4096",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=environment,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            model_url = f"http://127.0.0.1:{self.model_port}"
        else:
            # No model bundled. The Assistant still retrieves and still refuses
            # operational questions; it simply cannot phrase an answer. Said
            # plainly rather than presented as a general failure.
            self._last_error = "no local model is bundled with this installation"
            logger.warning("Assistant starting without a model: %s", self._last_error)

        if model_url:
            command = command + ["--model-url", model_url]

        self._child = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=environment,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        logger.info("Assistant process started (model=%s)", model_url or "none")
        return True

    def stop(self) -> None:
        with self._lock:
            for process, name in ((self._child, "assistant"), (self._model, "model server")):
                if process is None or process.poll() is not None:
                    continue
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    logger.warning("Assistant %s did not stop; killing", name)
                    process.kill()
            self._child = None
            self._model = None
            self._model_awaited = False

    # -- protocol -----------------------------------------------------------

    def _exchange(self, request: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if self._child is None or self._child.poll() is not None:
                if not self._start_locked():
                    return {"ok": False, "error": self._last_error}
            child = self._child
            assert child is not None and child.stdin and child.stdout

            try:
                child.stdin.write(json.dumps(request) + "\n")
                child.stdin.flush()
                line = _read_line(child, REQUEST_TIMEOUT)
            except _Timeout:
                # A read with no timeout, holding the lock, is how one wedged
                # child process freezes the whole application: every later
                # request blocks on the same lock until the server's worker
                # pool is exhausted and DairyOS stops answering anything.
                # The child is killed and replaced instead.
                logger.error("Assistant did not answer within %ss; restarting it", REQUEST_TIMEOUT)
                child.kill()
                self._child = None
                return {"ok": False, "error": "The AI Assistant stopped responding and was restarted."}
            except (BrokenPipeError, OSError) as exc:
                self._child = None
                return {"ok": False, "error": f"the Assistant process stopped: {exc}"}

            if not line:
                self._child = None
                return {"ok": False, "error": "the Assistant process stopped unexpectedly"}
            try:
                return json.loads(line)
            except json.JSONDecodeError as exc:
                return {"ok": False, "error": f"unreadable response from the Assistant: {exc}"}

    def ask(self, question: str) -> dict[str, Any]:
        # Start first, then wait. On the very first question the model process
        # does not exist yet, so waiting before starting would skip the wait
        # entirely and lose the answer it exists to protect.
        self.start()
        self._await_model_once()
        return self._exchange({"type": "ask", "question": question})

    def _await_model_once(self) -> None:
        """Give the model one bounded chance to finish loading.

        Loading 1.28 GB takes the better part of a minute on a farm machine.
        Without this, every question asked in that window failed to reach the
        model and fell back to the approved text, which looked to the operator
        like an Assistant that simply did not work.

        Bounded, and only on the first use: an operator watching a spinner will
        wait a little for the first answer of a session and should never wait
        again. If the model is still not ready when the wait expires, the
        question is answered from approved knowledge rather than held up.
        """
        if self._model_awaited or self._model is None or self._model.poll() is not None:
            return
        self._model_awaited = True
        if not self.wait_for_model(timeout=MODEL_FIRST_USE_WAIT):
            logger.warning(
                "Model not ready within %ss; answering from approved knowledge "
                "until it finishes loading.",
                MODEL_FIRST_USE_WAIT,
            )

    def status(self) -> dict[str, Any]:
        response = self._exchange({"type": "status"})
        if not response.get("ok"):
            return {"running": False, "error": response.get("error", "unavailable")}
        payload = dict(response.get("status", {}))
        payload["running"] = True
        payload["model_ready"] = self.model_ready()
        return payload

    def probe(self) -> dict[str, Any]:
        """Report readiness without starting anything.

        Deliberately distinct from ``status()``. Asking the Assistant for its
        status starts it if it is not running, which loads 1.28 GB of model
        weights. A diagnostic screen must never do that as a side effect of
        being opened, so this reads only what can be known without a
        conversation: whether the executable is installed, whether the model is
        bundled beside it, and whether the process happens to be running.

        An Assistant that has not started yet is not a fault. It starts on the
        first question by design.
        """
        command = assistant_command()
        runtime = model_paths()
        running = self._child is not None and self._child.poll() is None

        detail: dict[str, Any] = {
            "installed": command is not None,
            "model_bundled": runtime is not None,
            "running": running,
            "model_running": self.model_ready(),
        }
        if running:
            # Only ask when it is already up, so a probe never becomes a start.
            response = self._exchange({"type": "status"})
            if response.get("ok"):
                inner = response.get("status", {})
                detail["corpus_version"] = inner.get("corpus_version")
                detail["servable_items"] = inner.get("servable_items")
                detail["serving_unreviewed"] = inner.get("serving_unreviewed")
        return detail

    def self_test(self, timeout: float = 20.0) -> dict[str, Any]:
        """Exercise the Assistant end to end, without loading the model.

        Every other System Health entry performs a real read against the real
        database. An entry that merely confirmed a file exists would prove
        nothing, so this asks the Assistant two questions and checks the
        answers: one it should find knowledge for, and one it must refuse.

        The model is deliberately not started. Loading 1.28 GB would dominate
        the check, and it is not what a packaging error breaks. What this does
        exercise is everything that a bad build does break: the executable
        runs, the pipe works, the corpus is present and loads, retrieval
        returns the right item, and the refusal boundary holds.

        A throwaway process is used rather than the long-lived one, so a
        diagnostic never changes the state of the Assistant the operator is
        about to use.
        """
        result: dict[str, Any] = {
            "installed": False,
            "process_starts": False,
            "corpus_loads": False,
            "retrieval_works": False,
            "refuses_operational": False,
            "model_bundled": model_paths() is not None,
            "error": "",
        }

        command = assistant_command()
        if command is None:
            result["error"] = "the Assistant executable is not present"
            return result
        result["installed"] = True

        probe_requests = (
            {"type": "status"},
            {"type": "ask", "question": "What is a withdrawal period?"},
            {"type": "ask", "question": "How much milk did we produce today?"},
        )
        payload = "".join(json.dumps(r) + "\n" for r in probe_requests)

        try:
            child = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                env=sanitised_environment(),
            )
        except OSError as exc:
            result["error"] = f"the Assistant could not be started: {exc}"
            return result

        result["process_starts"] = True
        try:
            out, _ = child.communicate(payload, timeout=timeout)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate()
            result["error"] = f"the Assistant did not answer within {timeout:g}s"
            return result
        finally:
            if child.poll() is None:
                child.terminate()

        lines = [line for line in (out or "").splitlines() if line.strip()]
        try:
            responses = [json.loads(line) for line in lines]
        except json.JSONDecodeError as exc:
            result["error"] = f"unreadable response from the Assistant: {exc}"
            return result

        if len(responses) < 3:
            result["error"] = "the Assistant stopped before answering"
            return result

        status, knowledge, operational = responses[0], responses[1], responses[2]

        if status.get("ok"):
            inner = status.get("status", {})
            result["corpus_loads"] = bool(inner.get("servable_items"))
            result["corpus_version"] = inner.get("corpus_version")
            result["servable_items"] = inner.get("servable_items")
            result["serving_unreviewed"] = bool(inner.get("serving_unreviewed"))

        result["retrieval_works"] = bool(knowledge.get("ok") and knowledge.get("evidence"))
        result["refuses_operational"] = (
            operational.get("ok") is True
            and operational.get("decision") == "REFUSE_OPERATIONAL_DATA"
        )
        return result

    def model_ready(self) -> bool:
        return self._model is not None and self._model.poll() is None

    def wait_for_model(self, timeout: float = MODEL_READY_TIMEOUT) -> bool:
        """Wait for the model server to accept work.

        Loading 1.28 GB of weights takes time on a farm machine, and the first
        question would otherwise fail for a reason that looks like a fault.
        """
        if self._model is None:
            return False
        import urllib.error
        import urllib.request

        deadline = time.monotonic() + timeout
        url = f"http://127.0.0.1:{self.model_port}/health"
        while time.monotonic() < deadline:
            if self._model.poll() is not None:
                return False
            try:
                with urllib.request.urlopen(url, timeout=5.0) as response:
                    if 200 <= response.status < 300:
                        return True
            except (urllib.error.URLError, OSError):
                pass
            time.sleep(1.0)
        return False


bridge = AssistantBridge()
