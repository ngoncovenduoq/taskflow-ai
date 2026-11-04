
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from dashboard_api import router as dashboard_router
from agent import ask_agent_with_usage
from document_api import router as document_router
from api_errors import to_http_exception, upstream_status
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from task_api import router as task_router
from conversation_api import router as conversation_router
from chat_history import asks_about_prior_chat, get_recent_conversation_context

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

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

app.mount(
    "/ui",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend"
)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    conversation_id: int | None = Field(default=None, gt=0)

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message không được để trống")
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
        return ask_agent_with_usage(request.message, history=history)

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
