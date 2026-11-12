import socket
import subprocess
import sys
import time

import httpx
import pytest


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server():
    """Start the FastAPI service in a background subprocess on a free port."""
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "demo_api.main:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for _ in range(50):
        try:
            if httpx.get(f"{base_url}/api/status", timeout=1.0).status_code == 200:
                break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError("FastAPI test server failed to start within 5 seconds.")

    yield base_url

    proc.terminate()
    proc.wait()


@pytest.fixture(autouse=True)
def _reset_utcp_client():
    """Each test starts without a cached UTCP client."""
    import hermes_plugin.tools as tools_mod

    tools_mod.reset_client_cache()
    yield
    tools_mod.reset_client_cache()
