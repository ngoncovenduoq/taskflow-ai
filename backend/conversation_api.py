"""FastAPI routes for SQLite chat history; all operations are local and free."""

import logging
import sqlite3
from typing import Literal

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from chat_history import (
    init_chat_db,
    create_conversation,
    get_conversations,
    get_conversation_messages,
    add_conversation_message,
    delete_conversation,
)


router = APIRouter(prefix="/api/conversations", tags=["Conversations"])
logger = logging.getLogger(__name__)
init_chat_db()


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=20000)


@router.get("/")
def list_conversations() -> dict:
    try:
        return {"conversations": get_conversations()}
    except sqlite3.Error as error:
        logger.exception("Unable to load conversations")
        raise HTTPException(status_code=500, detail="Không thể đọc lịch sử hội thoại.") from error


@router.post("/", status_code=201)
def create_conversation_item() -> dict:
    try:
        return create_conversation()
    except sqlite3.Error as error:
        logger.exception("Unable to create conversation")
        raise HTTPException(status_code=500, detail="Không thể tạo hội thoại.") from error


@router.get("/{conversation_id}/messages")
def list_conversation_messages(conversation_id: int = Path(gt=0)) -> dict:
    try:
        messages = get_conversation_messages(conversation_id)
    except sqlite3.Error as error:
        logger.exception("Unable to read messages")
        raise HTTPException(status_code=500, detail="Không thể đọc tin nhắn.") from error
    if messages is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại.")
    return {"conversation_id": conversation_id, "messages": messages}


@router.post("/{conversation_id}/messages", status_code=201)
def create_conversation_message(payload: ConversationMessage, conversation_id: int = Path(gt=0)) -> dict:
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Nội dung tin nhắn không được để trống.")
    try:
        message = add_conversation_message(conversation_id, payload.role, payload.content)
    except sqlite3.Error as error:
        logger.exception("Unable to persist message")
        raise HTTPException(status_code=500, detail="Không thể lưu tin nhắn.") from error
    if message is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại.")
    return message


@router.delete("/{conversation_id}")
def delete_conversation_item(conversation_id: int = Path(gt=0)) -> dict:
    try:
        deleted = delete_conversation(conversation_id)
    except sqlite3.Error as error:
        logger.exception("Unable to delete conversation")
        raise HTTPException(status_code=500, detail="Không thể xóa hội thoại.") from error
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại.")
    return {"id": conversation_id, "deleted": True}
