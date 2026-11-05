# TaskFlow AI

**A local-first AI productivity assistant for task management, document Q&A, web research, writing, and usage analytics.**

TaskFlow AI combines a FastAPI backend with a lightweight web interface. It helps users organize their work, chat with an AI assistant, search their uploaded PDFs, research topics using web sources, and draft or export documents—all from one workspace.

The application runs on your own computer. AI features use real API calls through **OpenRouter**, while web research uses **Tavily**. Each person who clones the project configures their own API credentials; **no API keys are included in this repository**.

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

| Layer | Technologies |
| --- | --- |
| Backend | Python 3.10, FastAPI, Uvicorn, Pydantic |
| AI orchestration | LangChain, LangGraph, OpenRouter |
| PDF retrieval | pypdf, ChromaDB |
| Web search | Tavily API |
| Persistence | SQLite (tasks, conversations, research, drafts, and usage) |
| Frontend | HTML, CSS, vanilla JavaScript |
| Exports | python-docx, ReportLab |
| Testing | Python `unittest`; frontend mock tests |

## Quick start — Windows

### Prerequisites

- Windows with **Python 3.10** (including the `py` launcher) and Git installed.
- An Internet connection for package installation and external AI calls.
- **Your own OpenRouter API key** for AI chat, document answers, and writing.
- **Optional:** your own Tavily API key for web research.

### 1. Clone the repository

On GitHub, open this repository and copy its HTTPS URL from **Code → HTTPS**. Then open PowerShell:

```powershell
git clone YOUR_GITHUB_REPOSITORY_HTTPS_URL
cd taskflow-ai
```

Replace `taskflow-ai` in the second line with the actual cloned folder name if different.

### 2. Install dependencies and configure API access

From the repository root:

```powershell
.\SETUP.bat
```

The setup script:

1. Creates a local `.venv` with Python 3.10.
2. Installs dependencies from `requirements-lock.txt` when available (otherwise from `requirements.txt`, with a warning).
3. Checks the required backend and frontend files.
4. Prompts for your OpenRouter API key and, optionally, a Tavily API key. The characters are hidden while typing.
5. Saves these settings to **`backend/.env` on your computer only**.

**Important:** `backend/.env` contains plaintext credentials and is excluded by `.gitignore`. Do not commit, share, screenshot, or upload this file. For a demonstration on someone else's computer, use a separate, limited key and revoke it afterward.

### 3. Run the application

```powershell
.\START.bat
```

Once the server is healthy, your browser should open:

- **Application:** http://127.0.0.1:8000/ui/
- **Health check:** http://127.0.0.1:8000/health
- **Interactive API docs:** http://127.0.0.1:8000/docs

Press **Ctrl+C** in the server terminal to stop the app. On subsequent launches, run `START.bat` again; no reinstall or API-key re-entry is needed.

### Manual start (optional)

If you prefer PowerShell commands instead of the batch files:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe backend\check_release.py
.\.venv\Scripts\python.exe setup_local.py
.\.venv\Scripts\python.exe app_launcher.py
```

If the repository does not contain `requirements-lock.txt`, substitute `requirements.txt` and verify compatibility. You can also copy `backend/.env.example` to `backend/.env` and edit the values locally instead of using `setup_local.py`.

## Try it out

1. **Tasks:** Create a task and mark it complete; verify that Dashboard statistics update.
2. **Chat:** Ask the assistant a question, then create a new conversation to verify context separation.
3. **PDFs:** Upload a text-based PDF, index it, select it, and ask for a fact with a page reference.
4. **Research:** With Tavily configured, research a topic and review the linked sources.
5. **Writing:** Generate a draft, edit it, and export it to DOCX or PDF.
6. **Analytics:** Check the token and estimated-cost records after successful AI requests.
7. **Persistence:** Refresh the page or restart the application; verify saved data remains available.

## Tests and verification

Run the automated backend tests from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v
```

Test the clone/setup helpers:

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_local_run.py
```

**Reported results on the original Windows development machine (5 November 2026):** 41 backend unit tests passed, and eight manual integration scenarios passed. The generic setup/launcher test suite has eight passing tests. These results are **not** a guarantee for every future environment: rerun the tests after a fresh clone or dependency change. No public CI pipeline is claimed.

For a fresh-install checklist, see [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

## Project structure

```text
taskflow-ai/
├── SETUP.bat                 # First-time Windows setup
├── START.bat                 # Launch the local application
├── setup_local.py            # Local API-key configuration
├── app_launcher.py           # Backend launch and browser readiness
├── requirements.txt          # Direct dependencies
├── requirements-lock.txt     # Tested, pinned environment (recommended)
├── README.md
└── backend/
    ├── main.py               # FastAPI app and /ui mount
    ├── agent.py              # AI tools and model integration
    ├── supervisor.py         # AI request orchestration
    ├── task_api.py
    ├── conversation_api.py
    ├── document_api.py
    ├── research_api.py
    ├── writing_api.py
    ├── analytics_api.py
    ├── rag_store.py           # Document indexing/retrieval
    ├── .env.example           # Safe configuration template
    └── frontend/             # HTML, CSS, and JavaScript UI
        ├── index.html
        ├── app.js
        └── *.css
```

**Repository layout matters:** the frontend must be located at `backend/frontend/`, where FastAPI expects to serve it. Local databases, uploaded files, ChromaDB indexes, virtual environments, and real `.env` files should remain outside version control.

## Selected API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Application readiness |
| `POST` | `/chat` | AI chat and document questions |
| `GET / POST` | `/api/tasks/` | Task listing and creation |
| `GET / POST` | `/api/conversations/` | Conversation history and creation |
| `POST` | `/documents/upload` | PDF upload |
| `POST` | `/api/research/search` | Web research |
| `POST` | `/api/writing/generate` | AI draft generation |
| `GET` | `/api/analytics/overview` | AI usage summary |

The complete OpenAPI reference is available at `/docs` while the app is running.

## Security, limitations, and scope

- **Local-first:** the server binds to `127.0.0.1`; it is not a hosted multi-user service. The local browser protections are **not** a replacement for authentication and authorization.
- **Bring your own API keys:** neither a working OpenRouter key nor a Tavily key is distributed with the source. API usage may incur charges.
- **PDF support:** maximum upload size is 5 MB per PDF; scanned/image-only PDFs are not OCR-enabled.
- **Data storage:** SQLite records, documents, and search indexes stay on the current machine. Cloned installations do not share each other's local histories.
- **Cost reporting:** token and cost figures depend on provider metadata and available pricing; costs shown in the app are estimates, not invoices.
- **Deployment:** publicly hosting this backend would require authentication, per-user data isolation, HTTPS, rate limits, secret management, and additional security review.

## Roadmap

- Automated CI for the Python and frontend tests.
- Cross-platform install scripts and packaging beyond Windows.
- Optional OCR support for scanned PDFs.
- Authenticated deployment with user isolation and usage controls.

---

**TaskFlow AI is a portfolio project demonstrating a practical integration of AI tools, retrieval-augmented generation, persistent application state, and a usable local web interface.**
