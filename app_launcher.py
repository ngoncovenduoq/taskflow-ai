"""Start the normal local TaskFlow AI application and open its web interface."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
APP_URL = "http://127.0.0.1:8000/ui/"
HEALTH_URL = "http://127.0.0.1:8000/health"


def validate_project() -> list[str]:
    return [
        str(path.relative_to(ROOT))
        for path in (
            BACKEND / "main.py",
            BACKEND / "agent.py",
            BACKEND / "research_search.py",
            BACKEND / "writing_agent.py",
            BACKEND / "usage_tracker.py",
            BACKEND / "api_errors.py",
            BACKEND / "frontend" / "index.html",
        )
        if not path.is_file()
    ]


def port_is_free() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", 8000))
            return True
        except OSError:
            return False


def has_api_key() -> bool:
    """Honor an existing environment variable or the local ignored .env."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        from dotenv import dotenv_values

        key = (dotenv_values(BACKEND / ".env").get("OPENROUTER_API_KEY") or "").strip()
    return bool(key and "replace_with" not in key.lower())


def open_browser_when_ready(stopped: threading.Event) -> None:
    for _ in range(60):
        if stopped.is_set():
            return
        try:
            with urlopen(HEALTH_URL, timeout=0.5) as response:
                if response.status == 200 and json.load(response).get("status") == "ok":
                    webbrowser.open(APP_URL)
                    return
        except (OSError, URLError, ValueError, json.JSONDecodeError):
            pass
        stopped.wait(0.5)
    print("Backend chua san sang. Xem thong bao loi phia tren.")


def main() -> int:
    missing = validate_project()
    if missing:
        print("Thieu file backend/frontend trong repository:")
        for item in missing:
            print(f"  - {item}")
        return 1
    if not has_api_key():
        print("Chua co OPENROUTER_API_KEY. Chay SETUP.bat de cau hinh truoc.")
        return 1
    if not port_is_free():
        print("Cong 8000 dang duoc su dung. Hay tat TaskFlow AI dang chay truoc.")
        return 1

    stopped = threading.Event()
    browser_thread = threading.Thread(target=open_browser_when_ready, args=(stopped,), daemon=True)
    browser_thread.start()
    print("TaskFlow AI dang chay: http://127.0.0.1:8000/ui/")
    print("Nhan Ctrl+C trong cua so nay de dung ung dung.")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=BACKEND,
            check=False,
        )
        return result.returncode
    except KeyboardInterrupt:
        return 130
    finally:
        stopped.set()


if __name__ == "__main__":
    raise SystemExit(main())
