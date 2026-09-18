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
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
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
REQUEST_TIMEOUT = 90.0

# Kept deliberately small. A question that has not been answered in this long
# has failed, and an operator staring at a spinner is worse served than one
# told to try again.
ASSISTANT_START_TIMEOUT = 60.0


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


def assistant_command() -> list[str] | None:
    """How to start the Assistant, frozen or from source."""
    root = _bundle_root()
    frozen = root / ("DairyOSAssistant.exe" if os.name == "nt" else "DairyOSAssistant")
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
    root = _bundle_root()
    candidates = [
        (root / "_internal" / "assistant-runtime", root / "_internal" / "assistant-runtime"),
        (root / "assistant-runtime", root / "assistant-runtime"),
        (root / "runtime" / "assistant", root / "runtime" / "assistant"),
    ]
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
    _lock: threading.Lock = threading.Lock()
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
                line = child.stdout.readline()
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
        return self._exchange({"type": "ask", "question": question})

    def status(self) -> dict[str, Any]:
        response = self._exchange({"type": "status"})
        if not response.get("ok"):
            return {"running": False, "error": response.get("error", "unavailable")}
        payload = dict(response.get("status", {}))
        payload["running"] = True
        payload["model_ready"] = self.model_ready()
        return payload

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
