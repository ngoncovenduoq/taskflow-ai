"""Offline unit tests for TaskFlow dashboard counts."""

import unittest

from task_summary import summarize_tasks


class TaskSummaryTests(unittest.TestCase):

    def test_empty_database(self):
        self.assertEqual(summarize_tasks([]), {
            "total_tasks": 0,
            "unfinished_tasks": 0,
            "completed_tasks": 0,
            "completion_percent": 0.0,
            "has_tasks": False,
        })

    def test_pending_and_completed(self):
        summary = summarize_tasks([
            (1, "Read Report.pdf", "pending"),
            (2, "Write email", "completed"),
            (3, "Prepare CV", "pending"),
        ])
        self.assertEqual(summary["total_tasks"], 3)
        self.assertEqual(summary["unfinished_tasks"], 2)
        self.assertEqual(summary["completed_tasks"], 1)
        self.assertEqual(summary["completion_percent"], 33.3)
        self.assertTrue(summary["has_tasks"])

    def test_mixed_completed_statuses(self):
        summary = summarize_tasks([
            (1, "A", "COMPLETED"),
            (2, "B", " done "),
            (3, "C", "Hoàn thành"),
            (4, "D", "in_progress"),
        ])
        self.assertEqual(summary["completed_tasks"], 3)
        self.assertEqual(summary["unfinished_tasks"], 1)
        self.assertEqual(summary["completion_percent"], 75.0)

    def test_all_completed(self):
        summary = summarize_tasks([(10, "Task", "completed")])
        self.assertEqual(summary["completion_percent"], 100.0)
        self.assertEqual(summary["unfinished_tasks"], 0)


if __name__ == "__main__":
    unittest.main()
