"""Local SQLite history for the dedicated Research workspace."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).with_name("research_history.db")


@contextmanager
def _connection():
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


def init_research_db():
    with _connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS research_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                summary TEXT NOT NULL,
                sources_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def _to_item(row):
    item = dict(row)
    item["sources"] = json.loads(item.pop("sources_json"))
    return item


def save_research(query: str, summary: str, sources: list[dict]) -> dict:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connection() as connection:
        cursor = connection.execute(
            "INSERT INTO research_history (query, summary, sources_json, created_at) VALUES (?, ?, ?, ?)",
            (query, summary, json.dumps(sources, ensure_ascii=False), created_at),
        )
        return {
            "id": int(cursor.lastrowid), "query": query, "summary": summary,
            "sources": sources, "created_at": created_at,
        }


def list_research(limit: int = 40) -> list[dict]:
    with _connection() as connection:
        rows = connection.execute(
            "SELECT * FROM research_history ORDER BY id DESC LIMIT ?",
            (min(max(limit, 1), 100),),
        ).fetchall()
    return [_to_item(row) for row in rows]


def delete_research(item_id: int) -> bool:
    with _connection() as connection:
        cursor = connection.execute("DELETE FROM research_history WHERE id = ?", (item_id,))
        return cursor.rowcount > 0
