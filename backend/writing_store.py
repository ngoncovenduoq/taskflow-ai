"""SQLite storage for drafts authored or edited in TaskFlow AI."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).with_name("writing_history.db")


@contextmanager
def _db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_writing_db():
    with _db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS writing_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                kind TEXT NOT NULL,
                tone TEXT NOT NULL,
                prompt TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_draft(title: str, kind: str, tone: str, prompt: str, content: str) -> dict:
    now = _now()
    with _db() as connection:
        cursor = connection.execute(
            """INSERT INTO writing_documents
               (title, kind, tone, prompt, content, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, kind, tone, prompt, content, now, now),
        )
        return {"id": cursor.lastrowid, "title": title, "kind": kind, "tone": tone,
                "prompt": prompt, "content": content, "created_at": now, "updated_at": now}


def get_draft(draft_id: int) -> dict | None:
    with _db() as connection:
        row = connection.execute("SELECT * FROM writing_documents WHERE id = ?", (draft_id,)).fetchone()
    return dict(row) if row else None


def list_drafts(limit: int = 40) -> list[dict]:
    with _db() as connection:
        rows = connection.execute(
            """SELECT id, title, kind, tone, created_at, updated_at
               FROM writing_documents ORDER BY updated_at DESC, id DESC LIMIT ?""",
            (min(max(limit, 1), 100),),
        ).fetchall()
    return [dict(row) for row in rows]


def update_draft(draft_id: int, title: str, content: str, tone: str) -> dict | None:
    with _db() as connection:
        cursor = connection.execute(
            "UPDATE writing_documents SET title = ?, content = ?, tone = ?, updated_at = ? WHERE id = ?",
            (title, content, tone, _now(), draft_id),
        )
        if not cursor.rowcount:
            return None
        row = connection.execute("SELECT * FROM writing_documents WHERE id = ?", (draft_id,)).fetchone()
        return dict(row)


def delete_draft(draft_id: int) -> bool:
    with _db() as connection:
        cursor = connection.execute("DELETE FROM writing_documents WHERE id = ?", (draft_id,))
        return cursor.rowcount > 0
