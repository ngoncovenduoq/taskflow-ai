"""SQLite persistence for TaskFlow AI conversation history (no LLM calls)."""

import sqlite3
import re
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).with_name("chat_history.db")


def asks_about_prior_chat(message: str) -> bool:
    """Recognize explicit recall questions, not ordinary PDF/task questions.

    This intentionally uses narrow matching: a fresh conversation must not
    invent memories, but users must still be able to ask about shared PDFs.
    """
    normalized = unicodedata.normalize("NFD", message.lower().replace("đ", "d"))
    normalized = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    normalized = " ".join(normalized.split())

    past_reference = any(phrase in normalized for phrase in (
        "luc nay", "khi nay", "hoi nay", "vua roi", "vua nay",
        "vua noi", "truoc do", "hom truoc", "lan truoc",
        "cuoc tro chuyen truoc", "earlier", "previously",
        "last time", "before this chat",
    ))
    personal_reference = re.search(r"\b(toi|minh|chung ta|ban|i|we|you)\b", normalized)
    recall_question = re.search(r"\b(gi|nao|what|which|remember|recall)\b", normalized)

    return bool(past_reference and personal_reference and recall_question)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


@contextmanager
def _connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_chat_db() -> None:
    with _connection() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'Cuộc trò chuyện mới',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_messages_parent
            ON conversation_messages(conversation_id, id)
        """)


def create_conversation() -> dict:
    timestamp = _utc_now()
    with _connection() as db:
        cursor = db.execute(
            "INSERT INTO conversations (title, created_at, updated_at) VALUES (?, ?, ?)",
            ("Cuộc trò chuyện mới", timestamp, timestamp),
        )
        return {
            "id": int(cursor.lastrowid),
            "title": "Cuộc trò chuyện mới",
            "created_at": timestamp,
            "updated_at": timestamp,
        }


def get_conversations(limit: int = 50) -> list[dict]:
    with _connection() as db:
        rows = db.execute("""
            SELECT c.id, c.title, c.created_at, c.updated_at,
                   COUNT(m.id) AS message_count
            FROM conversations AS c
            LEFT JOIN conversation_messages AS m ON m.conversation_id = c.id
            GROUP BY c.id
            ORDER BY c.updated_at DESC, c.id DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]


def get_conversation_messages(conversation_id: int, limit: int = 200) -> list[dict] | None:
    with _connection() as db:
        exists = db.execute(
            "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if exists is None:
            return None
        newest = db.execute("""
            SELECT id, role, content, created_at
            FROM conversation_messages
            WHERE conversation_id = ?
            ORDER BY id DESC LIMIT ?
        """, (conversation_id, limit)).fetchall()
        return [dict(row) for row in reversed(newest)]


def get_recent_conversation_context(
    conversation_id: int,
    current_message: str,
    max_turns: int = 4,
    max_chars: int = 6000,
) -> list[dict[str, str]] | None:
    """Return a bounded history of completed exchanges for the model.

    The UI saves the new user prompt before it calls /chat, so that prompt
    must not appear twice. Incomplete user turns (for example after an API
    failure) are not replayed as instructions to the model.
    """
    if max_turns < 1 or max_chars < 2:
        raise ValueError("Conversation limits must be positive.")

    with _connection() as db:
        exists = db.execute(
            "SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if exists is None:
            return None
        newest = db.execute("""
            SELECT role, content
            FROM conversation_messages
            WHERE conversation_id = ?
            ORDER BY id DESC LIMIT ?
        """, (conversation_id, max(20, max_turns * 8))).fetchall()

    messages = [dict(row) for row in reversed(newest)]
    if (messages and messages[-1]["role"] == "user"
            and messages[-1]["content"] == current_message):
        messages.pop()

    pairs = []
    pending_user = None
    for message in messages:
        if message["role"] == "user":
            pending_user = message["content"]
        elif message["role"] == "assistant" and pending_user is not None:
            pairs.append((pending_user, message["content"]))
            pending_user = None

    def clipped(content: str, limit: int) -> str:
        return content if len(content) <= limit else content[:limit - 1] + "…"

    selected = []
    remaining = max_chars
    for user_text, assistant_text in reversed(pairs[-max_turns:]):
        user_text = clipped(user_text, 900)
        assistant_text = clipped(assistant_text, 1200)
        total_length = len(user_text) + len(assistant_text)
        if total_length > remaining:
            break  # Prefer consecutive recent context, never disconnected older turns.
        selected.append((user_text, assistant_text))
        remaining -= total_length

    return [
        {"role": role, "content": content}
        for user_text, assistant_text in reversed(selected)
        for role, content in (("user", user_text), ("assistant", assistant_text))
    ]


def add_conversation_message(conversation_id: int, role: str, content: str) -> dict | None:
    if role not in {"user", "assistant"} or not content.strip():
        raise ValueError("Vai trò hoặc nội dung không hợp lệ.")
    timestamp = _utc_now()
    with _connection() as db:
        conversation = db.execute(
            "SELECT id, title FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if conversation is None:
            return None

        cursor = db.execute("""
            INSERT INTO conversation_messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
        """, (conversation_id, role, content, timestamp))

        title = conversation["title"]
        if role == "user" and title == "Cuộc trò chuyện mới":
            title = " ".join(content.split())[:60] or title
            if len(" ".join(content.split())) > 60:
                title = title.rstrip() + "…"
        db.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, timestamp, conversation_id),
        )
        return {
            "id": int(cursor.lastrowid),
            "role": role,
            "content": content,
            "created_at": timestamp,
        }


def delete_conversation(conversation_id: int) -> bool:
    with _connection() as db:
        cursor = db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        return cursor.rowcount > 0
