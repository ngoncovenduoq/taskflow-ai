
from fastapi import FastAPI
from pydantic import BaseModel

from agent import ask_agent

app = FastAPI(
    title="TaskFlow AI",
    description="My First AI Agent Project",
    version="1.0.0"
)


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
    answer = ask_agent(request.message)

    return {
        "response": answer
    }
