"""TaskFlow's SQLite task storage with non-destructive v7 column migration.

Existing agent methods (add_task/get_tasks/complete_task/delete_task) retain
their signatures and return shapes for backward compatibility.
"""

import sqlite3
from datetime import date
from pathlib import Path


DB_PATH = Path(__file__).with_name("tasks.db")
PRIORITIES = frozenset({"low", "medium", "high"})


def init_db():
    """Create or upgrade the existing tasks table without dropping any rows."""

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                priority TEXT NOT NULL DEFAULT 'medium',
                due_date TEXT
            )
        """)

        # SQLite CREATE TABLE IF NOT EXISTS does not alter an old table.
        columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
        if "priority" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")
        if "due_date" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")

        conn.commit()
    finally:
        conn.close()


def _validated_metadata(priority: str, due_date: str | None) -> tuple[str, str | None]:
    if priority not in PRIORITIES:
        raise ValueError("priority must be low, medium or high")
    if due_date is not None:
        if not isinstance(due_date, str) or len(due_date) != 10:
            raise ValueError("due_date must use YYYY-MM-DD format")
        try:
            date.fromisoformat(due_date)
        except ValueError as error:
            raise ValueError("due_date is not a valid calendar date") from error
    return priority, due_date


def add_task(title: str, priority: str = "medium", due_date: str | None = None) -> int:
    """Create a task; older agent calls with only title keep working."""

    priority, due_date = _validated_metadata(priority, due_date)
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "INSERT INTO tasks (title, priority, due_date) VALUES (?, ?, ?)",
            (title, priority, due_date),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_tasks():
    """Keep the original three-column format expected by the AI agent."""

    conn = sqlite3.connect(DB_PATH)
    try:
        return conn.execute(
            "SELECT id, title, status FROM tasks ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


def get_tasks_detailed():
    """Return five columns for the direct task manager."""

    conn = sqlite3.connect(DB_PATH)
    try:
        return conn.execute(
            "SELECT id, title, status, priority, due_date FROM tasks ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


def update_task(task_id: int, title: str, priority: str, due_date: str | None) -> bool:
    """Update editable task fields without changing its completion status."""

    title = title.strip()
    if not title:
        raise ValueError("title cannot be empty")
    priority, due_date = _validated_metadata(priority, due_date)
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "UPDATE tasks SET title = ?, priority = ?, due_date = ? WHERE id = ?",
            (title, priority, due_date, task_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def complete_task(task_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "UPDATE tasks SET status = 'completed' WHERE id = ?",
            (task_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def reopen_task(task_id: int) -> bool:
    """Undo completion without recreating the task or changing its ID."""

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "UPDATE tasks SET status = 'pending' WHERE id = ?",
            (task_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_task(task_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
