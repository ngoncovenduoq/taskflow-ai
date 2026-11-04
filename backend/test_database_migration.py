"""Offline regression tests for the additive SQLite v7 upgrade."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database


class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.db_path = Path(temp_dir.name) / "tasks.db"
        db_patch = patch.object(database, "DB_PATH", self.db_path)
        db_patch.start()
        self.addCleanup(db_patch.stop)

    def test_upgrade_old_schema_preserves_rows_and_ids(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending'
                )
            """)
            conn.execute("INSERT INTO tasks (title, status) VALUES (?, ?)", ("Đi học NLP", "pending"))
            conn.execute("INSERT INTO tasks (title, status) VALUES (?, ?)", ("Read report", "completed"))

        database.init_db()
        database.init_db()  # Re-running after Uvicorn reload is safe.
        self.assertEqual(database.get_tasks(), [
            (1, "Đi học NLP", "pending"),
            (2, "Read report", "completed"),
        ])
        self.assertEqual(database.get_tasks_detailed(), [
            (1, "Đi học NLP", "pending", "medium", None),
            (2, "Read report", "completed", "medium", None),
        ])

        with sqlite3.connect(self.db_path) as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
        self.assertTrue({"id", "title", "status", "priority", "due_date"}.issubset(columns))

    def test_new_task_metadata_and_legacy_agent_calls(self):
        database.init_db()
        old_agent_task_id = database.add_task("Agent tạo task")
        ui_task_id = database.add_task("Ôn NLP", "high", "2026-11-10")
        self.assertEqual(database.get_tasks(), [
            (old_agent_task_id, "Agent tạo task", "pending"),
            (ui_task_id, "Ôn NLP", "pending"),
        ])
        self.assertEqual(database.get_tasks_detailed()[1][3:], ("high", "2026-11-10"))

        self.assertTrue(database.complete_task(ui_task_id))
        self.assertTrue(database.reopen_task(ui_task_id))
        self.assertEqual(database.get_tasks()[1][2], "pending")
        self.assertTrue(database.update_task(ui_task_id, "Ôn tập NLP", "low", None))
        self.assertEqual(database.get_tasks_detailed()[1][1:], ("Ôn tập NLP", "pending", "low", None))
        self.assertTrue(database.delete_task(old_agent_task_id))
        self.assertFalse(database.reopen_task(old_agent_task_id))

    def test_invalid_metadata_and_unknown_id(self):
        database.init_db()
        with self.assertRaises(ValueError):
            database.add_task("Test", "critical", None)
        with self.assertRaises(ValueError):
            database.add_task("Test", "high", "2026-02-31")
        with self.assertRaises(ValueError):
            database.update_task(1, "  ", "low", None)
        self.assertFalse(database.update_task(999, "Not found", "medium", None))


if __name__ == "__main__":
    unittest.main()
