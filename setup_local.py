"""First-run configuration for a cloned TaskFlow AI installation.

The API key belongs to whoever runs this clone. It is stored only in the
ignored, local backend/.env file and is never added to Git automatically.
"""

import getpass
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / "backend" / ".env"


def configure_api_keys(env_file: Path = ENV_FILE, ask_secret=None) -> int:
    if env_file.exists():
        print(f"Da co {env_file.parent.name}/.env; khong ghi de cau hinh hien tai.")
        print("Muon thay API key, sua backend/.env tren may cua ban.")
        return 0

    if ask_secret is None:
        ask_secret = getpass.getpass

    print("\n=== CAU HINH TASKFLOW AI LAN DAU ===")
    print("Ban can OpenRouter API key cua rieng minh de dung AI that.")
    print("Key se luu duoi dang van ban trong backend/.env TREN MAY NAY.")
    print("Khong su dung key chinh cua nguoi khac tren may khong tin cay.")

    try:
        router_key = ask_secret("OpenRouter API key (an ky tu): ").strip()
        if not router_key or "replace_with" in router_key.lower():
            print("Chua nhap OpenRouter API key hop le. Chay lai SETUP.bat sau.")
            return 1
        tavily_key = ask_secret("Tavily API key (Enter de bo qua nghien cuu web): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nDa huy cau hinh.")
        return 1

    if any("\n" in value or "\r" in value for value in (router_key, tavily_key)):
        print("API key khong hop le.")
        return 1

    # JSON double-quoted strings are also accepted by python-dotenv.
    contents = (
        "# Cau hinh rieng tren may nay. KHONG COMMIT FILE NAY LEN GITHUB.\n"
        f"OPENROUTER_API_KEY={json.dumps(router_key)}\n"
        f"TAVILY_API_KEY={json.dumps(tavily_key)}\n"
        "OPENROUTER_MODEL=openai/gpt-oss-20b\n"
        "ROUTER_MODEL=openai/gpt-oss-20b\n"
    )
    env_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with env_file.open("x", encoding="utf-8") as stream:
            stream.write(contents)
    except FileExistsError:
        print("backend/.env vua duoc tao; khong ghi de.")
        return 1
    finally:
        del router_key, tavily_key, contents

    print("Da luu backend/.env cuc bo. Khong commit file nay len GitHub.")
    return 0


def main() -> int:
    try:
        return configure_api_keys()
    except OSError as exc:
        print(f"Khong luu duoc cau hinh: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
