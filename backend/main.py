
from fastapi import FastAPI
from pydantic import BaseModel

from agent import ask_agent
from document_api import router as document_router
from groq import RateLimitError
from fastapi import HTTPException

app = FastAPI(
    title="TaskFlow AI",
    description="My First AI Agent Project",
    version="1.0.0"
)
app.include_router(document_router)

class ChatRequest(BaseModel):
    message: str


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
        answer = ask_agent(request.message)

        return {
            "response": answer
        }

    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail=(
                "Groq Free da het han muc token. "
                "Vui long thu lai khi han muc duoc lam moi."
            )
        )
