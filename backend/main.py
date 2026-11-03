
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from agent import ask_agent_with_usage
from document_api import router as document_router
from api_errors import to_http_exception, upstream_status
from pathlib import Path
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

app = FastAPI(
    title="TaskFlow AI",
    description="My First AI Agent Project",
    version="1.0.0"
)
app.include_router(document_router)

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

app.mount(
    "/ui",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend"
)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)

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
        return ask_agent_with_usage(request.message)

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
