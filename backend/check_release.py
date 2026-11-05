"""Read-only preflight checks before packaging TaskFlow AI for local use."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import os
import sys


BACKEND = Path(__file__).resolve().parent
ROOT = BACKEND.parent
REQUIRED_MODULES = (
    "main.py", "agent.py", "supervisor.py", "security.py", "document_api.py",
    "research_api.py", "writing_api.py", "analytics_api.py", "usage_history.py",
    "api_errors.py", "usage_tracker.py", "research_search.py", "writing_agent.py",
)
PACKAGES = (
    "fastapi", "uvicorn", "pydantic", "python-multipart", "python-dotenv",
    "langchain", "langchain-core", "langchain-openrouter", "langgraph",
    "chromadb", "pypdf", "tavily-python", "requests", "python-docx", "reportlab",
)


def main() -> int:
    missing = []
    print("TaskFlow AI — kiểm tra trước phát hành (không gọi AI, không đọc key)")
    print(f"Python: {sys.version.split()[0]}")

    for name in REQUIRED_MODULES:
        if not (BACKEND / name).is_file():
            missing.append(f"backend/{name}")
    for name in ("index.html", "app.js"):
        if not (BACKEND / "frontend" / name).is_file():
            missing.append(f"backend/frontend/{name}")
    for package in PACKAGES:
        try:
            version(package)
        except PackageNotFoundError:
            missing.append(f"Thư viện: {package}")

    if missing:
        print("\nCẦN BỔ SUNG / KIỂM TRA:")
        for name in missing:
            print(f"  - {name}")
    else:
        print("[OK] Có đủ các module, giao diện và thư viện đã liệt kê.")

    if not (BACKEND / ".env").is_file() and not os.getenv("OPENROUTER_API_KEY"):
        print("[NHẮC] Chưa thấy backend/.env hoặc OPENROUTER_API_KEY trong môi trường.")
    if not (ROOT / ".gitignore").is_file():
        print("[NHẮC] Chưa thấy .gitignore ở thư mục gốc.")
    print("Lưu ý: chưa xác nhận API key, an toàn Internet hay tương thích phiên bản.")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
