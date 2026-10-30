"""
One-Click Local Launcher for Model 1: Report Structuring & Classification AI (SIH 2026).
Automatically:
1. Finds an open port (8080 or 8000).
2. Launches FastAPI & ML pipelines.
3. Automatically opens the interactive UI in your default browser.
"""

import os
import sys
import socket
import webbrowser
import threading
import time
from pathlib import Path
import uvicorn

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def find_free_port(preferred_ports=(8080, 8000, 8081, 8082)) -> int:
    for port in preferred_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    # Fallback to ephemeral port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def open_browser(url: str, delay: float = 1.5):
    def _open():
        time.sleep(delay)
        print(f"\n[Launcher] Opening browser at {url} ...")
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    env_port = os.environ.get("PORT")
    port = int(env_port) if env_port else find_free_port()
    display_host = "localhost" if host == "0.0.0.0" else host
    url = f"http://{display_host}:{port}"
    headless = os.environ.get("HEADLESS", "0").lower() in ("1", "true", "yes")

    print("=" * 75)
    print("  🚀 SIH 2026: Model 1 — Report Structuring & Classification AI")
    print("=" * 75)
    print(f"  • Host / Binding      : {host}:{port}")
    print(f"  • Interactive Demo UI : {url}")
    print(f"  • Swagger API Docs    : {url}/docs")
    print(f"  • Health Check        : {url}/health")
    print("=" * 75)
    print("  Press Ctrl + C to stop the server.\n")

    # Auto-launch browser tab if not in headless/container mode
    if not headless:
        open_browser(url)

    # Start FastAPI
    uvicorn.run("src.api.app:app", host=host, port=port, reload=False)



if __name__ == "__main__":
    main()
