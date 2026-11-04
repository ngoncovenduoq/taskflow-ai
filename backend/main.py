
import logging
import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from dashboard_api import router as dashboard_router
from agent import ask_agent_with_usage, ask_pdf_with_usage, ask_pdfs_with_usage
from document_api import router as document_router
from api_errors import to_http_exception, upstream_status
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from task_api import router as task_router
from conversation_api import router as conversation_router
from research_api import router as research_router
from writing_api import router as writing_router
from analytics_api import router as analytics_router
from usage_history import record_usage_safely
from chat_history import asks_about_prior_chat, get_recent_conversation_context
from rag_store import list_documents

logger = logging.getLogger(__name__)

app = FastAPI(
    title="TaskFlow AI",
    description="My First AI Agent Project",
    version="1.0.0"
)
app.include_router(dashboard_router)
app.include_router(document_router)
app.include_router(task_router)
app.include_router(conversation_router)
app.include_router(research_router)
app.include_router(writing_router)
app.include_router(analytics_router)

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

app.mount(
    "/ui",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend"
)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    conversation_id: int | None = Field(default=None, gt=0)
    document_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    document_ids: list[str] | None = Field(default=None, min_length=1, max_length=5)

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message không được để trống")
        return value

    @field_validator("document_ids")
    @classmethod
    def valid_document_ids(cls, value: list[str] | None) -> list[str] | None:
        if value is not None:
            if any(not re.fullmatch(r"[0-9a-f]{32}", item) for item in value):
                raise ValueError("ID tài liệu không hợp lệ.")
            if len(value) != len(set(value)):
                raise ValueError("Không chọn trùng tài liệu PDF.")
        return value


@app.get("/")
def home():
    return {
        "message": "Welcome to TaskFlow AI!"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):

    try:
        history = []
        if request.conversation_id is not None:
            history = get_recent_conversation_context(
                request.conversation_id, request.message
            )
            if history is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại.")

        # An empty chat has no personal conversation memories.  A PDF indexed
        # elsewhere is not evidence of what this user said in this chat.
        # Resolve explicit memory-recall questions locally, without LLM cost.
        if not history and asks_about_prior_chat(request.message):
            return {
                "response": (
                    "Mình chưa có thông tin về nội dung trò chuyện trước đó "
                    "trong cuộc trò chuyện này. Bạn có thể nhắc lại chủ đề "
                    "để mình hỗ trợ tiếp nhé!"
                ),
                "usage": {
                    "route": "local_memory",
                    "usage_available": True,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "reasoning_tokens": 0,
                    "estimated_cost_usd": 0,
                    "duration_ms": 0,
                    "by_model": [],
                },
            }
        if request.document_id is not None and request.document_ids is not None:
            raise HTTPException(status_code=422, detail="Chỉ dùng document_id hoặc document_ids.")
        selected_ids = request.document_ids or ([request.document_id] if request.document_id else [])
        if selected_ids:
            available = {item["document_id"]: item for item in list_documents()}
            for document_id in selected_ids:
                document = available.get(document_id)
                if document is None:
                    raise HTTPException(status_code=404, detail="Không tìm thấy một PDF đã chọn.")
                if not document["indexed"]:
                    raise HTTPException(status_code=409, detail=f"PDF chưa lập chỉ mục: {document['filename']}.")
            if len(selected_ids) == 1:
                result = ask_pdf_with_usage(request.message, selected_ids[0], history=history)
            else:
                result = ask_pdfs_with_usage(request.message, selected_ids, history=history)
        else:
            result = ask_agent_with_usage(request.message, history=history)
        record_usage_safely(result.get("usage"))
        return result

    except HTTPException:
        raise

    except Exception as error:
        # Do not log full exception text: SDK errors may contain prompt data.
        logger.error(
            "Chat failed: type=%s upstream_status=%s",
            type(error).__name__,
            upstream_status(error),
        )
        raise to_http_exception(error) from error
