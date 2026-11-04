
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("tasks.db")


# 1. Create database table
def init_db():
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            )
        """)

        conn.commit()
    finally:
        conn.close()


# 2. Create task
def add_task(title: str) -> int:
    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.execute(
            "INSERT INTO tasks (title) VALUES (?)",
            (title,)
        )

        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# 3. Read tasks
def get_tasks():
    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.execute(
            "SELECT id, title, status FROM tasks ORDER BY id"
        )

        return cursor.fetchall()
    finally:
        conn.close()


# 4. Complete task
def complete_task(task_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET status = 'completed'
            WHERE id = ?
            """,
            (task_id,)
        )

        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# 5. Delete task
def delete_task(task_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )

        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
