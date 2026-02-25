"""
Pytest session fixture: starts the FastAPI backend on port 8000 for the
test session, or reuses one that is already running.
"""
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
BASE_URL = "http://localhost:8000"
_TIMEOUT = 30          # seconds to wait for the server to become ready
_OWN_PROCESS: subprocess.Popen | None = None


def _server_ready() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def server():
    """
    Start the backend server once per test session.
    If localhost:8000 already responds, we reuse it (no-op teardown).
    Otherwise we spawn uvicorn and kill it when done.
    """
    global _OWN_PROCESS

    if _server_ready():
        # Already running – nothing to manage
        yield BASE_URL
        return

    _OWN_PROCESS = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "main:app",
            "--port", "8000",
            "--log-level", "warning",
        ],
        cwd=BACKEND_DIR,
    )

    deadline = time.monotonic() + _TIMEOUT
    while time.monotonic() < deadline:
        if _server_ready():
            break
        time.sleep(0.4)
    else:
        _OWN_PROCESS.terminate()
        pytest.fail(f"Backend did not become ready within {_TIMEOUT}s")

    yield BASE_URL

    _OWN_PROCESS.terminate()
    _OWN_PROCESS.wait(timeout=10)
