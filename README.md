# TaskFlow AI

**A local-first AI productivity assistant built with Python, FastAPI, and LangChain.**

TaskFlow AI brings task management, AI chat, PDF question answering, web research, document writing, and usage analytics into one web workspace. It runs locally on Windows and uses real AI APIs.

## Features

| Feature | What it does |
| --- | --- |
| **Task management & dashboard** | Create, update, complete, reopen, and delete tasks; track deadlines and progress. |
| **AI chat & conversation history** | Chat with an AI assistant, save conversations, reopen previous messages, and keep conversations isolated. |
| **PDF knowledge base (RAG)** | Upload text-based PDFs, index them, ask document-grounded questions, and receive source/page references. Supports selecting multiple indexed PDFs. |
| **Web research** | Retrieve web search results, generate a source-linked summary, and save research history. |
| **AI writing** | Generate and revise drafts, edit saved content, and export TXT, DOCX, or PDF files. |
| **AI usage analytics** | View recorded calls, token counts, estimated model costs, and daily/weekly/monthly summaries. |
| **Resizable workspace** | Expand chat and research areas for longer responses. |

## Tech stack

| Component | Technologies |
| --- | --- |
| Backend & API | Python 3.10, FastAPI, Pydantic, Uvicorn |
| AI & retrieval | LangChain, LangGraph, OpenRouter, ChromaDB, pypdf |
| Research | Tavily API |
| Data & frontend | SQLite, HTML, CSS, JavaScript |
| Document export | python-docx, ReportLab |

## Quick start (Windows)

**Requirements:** Git, Python 3.10 (`py` launcher), Internet connection, and your own **OpenRouter API key**. A **Tavily API key** is optional for web research.

1. **Clone** the repository (replace `USERNAME` with the GitHub account):

   ```powershell
   git clone https://github.com/USERNAME/taskflow-ai.git
   cd taskflow-ai
   ```

2. **Install and configure** (first run only):

   ```powershell
   .\SETUP.bat
   ```

   This creates `.venv`, installs dependencies from `requirements-lock.txt`, checks the project, and prompts for API keys. Keys are stored locally in `backend/.env`.

3. **Launch:**

   ```powershell
   .\START.bat
   ```

   Open **http://127.0.0.1:8000/ui/** if the browser does not open automatically. Stop the server with `Ctrl+C`; use `START.bat` for later sessions.

**API keys are not included in the repository.** Never commit or share `backend/.env`. API calls may incur charges. If `requirements-lock.txt` is unavailable, `SETUP.bat` falls back to the unpinned `requirements.txt` with a warning.

## Try the app

1. Create a task and verify the dashboard updates.
2. Ask the AI a question, start another conversation, and check conversation isolation.
3. Upload a text-based PDF, index it, and request an answer with a page reference.
4. Try web research (with Tavily configured), generate a draft, and export it.
5. Refresh or restart the app to verify saved data persists.

## Testing

Run automated tests from the repository root after setup:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v
.\.venv\Scripts\python.exe -m unittest -v test_local_run.py
```

**Verified on the original Windows development machine (November 2026):** 41 backend unit tests and 8 manual integration scenarios passed. The local setup/launcher suite has 8 passing tests. Results should be rechecked after cloning or updating dependencies.

For detailed checks, see [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). API documentation is available at **http://127.0.0.1:8000/docs** when running.

## Repository layout

```text
taskflow-ai/
├── SETUP.bat / START.bat      # One-time setup / local launch
├── setup_local.py / app_launcher.py
├── requirements-lock.txt
└── backend/
    ├── main.py               # FastAPI entry point
    ├── agent.py              # AI integration
    ├── rag_store.py          # PDF retrieval
    ├── ... API and storage modules ...
    └── frontend/             # HTML, CSS, JavaScript
```

## Current scope

- Runs on **localhost (`127.0.0.1`)**; not a hosted multi-user service.
- PDFs are limited to **5 MB** each; scanned PDFs do not have OCR support.
- SQLite data and PDF indexes stay on the user's machine. Usage costs are **estimates**, not invoices.
- Public deployment would require authentication, user isolation, rate limits, and additional security work.

**Next steps:** Add CI, improve cross-platform setup, and explore OCR support.
