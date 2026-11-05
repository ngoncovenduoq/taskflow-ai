"""Tests for persistent AI usage metrics and Vietnam-local time grouping."""

from datetime import datetime
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


BACKEND = Path(__file__).parent
sys.path.insert(0, str(BACKEND))
import usage_history  # noqa: E402


class UsageHistoryTests(unittest.TestCase):
    def test_persisted_usage_and_calendar_aggregates(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "usage.db"
            with patch.object(usage_history, "DB_PATH", path):
                usage_history.init_usage_db()
                first = usage_history.record_usage({
                    "route": "general", "usage_available": True,
                    "total_tokens": 140, "input_tokens": 100, "output_tokens": 40,
                    "reasoning_tokens": 10, "estimated_cost_usd": 0.00056,
                    "duration_ms": 1300,
                    "by_model": [{"model": "provider/model", "total_tokens": 140,
                                  "estimated_cost_usd": 0.00056, "secret_prompt": "DO NOT STORE"}],
                    "message": "Private question DO NOT STORE",
                })
                second = usage_history.record_usage({
                    "route": "writing", "usage_available": False,
                    "total_tokens": None, "estimated_cost_usd": None,
                })
                old = usage_history.record_usage({
                    "route": "pdf", "usage_available": True,
                    "total_tokens": 50, "estimated_cost_usd": 0.0001,
                })
                self.assertIsNone(usage_history.record_usage({"route": "local_memory", "total_tokens": 0}))
                with usage_history._db() as connection:
                    connection.execute("UPDATE ai_usage_events SET created_at = ? WHERE id = ?",
                                       ("2026-11-04T03:30:00+00:00", first))
                    connection.execute("UPDATE ai_usage_events SET created_at = ? WHERE id = ?",
                                       ("2026-11-02T19:30:00+00:00", second))
                    connection.execute("UPDATE ai_usage_events SET created_at = ? WHERE id = ?",
                                       ("2026-10-31T14:00:00+00:00", old))
                now = datetime(2026, 11, 4, 14, tzinfo=usage_history.LOCAL_TZ)
                day = usage_history.get_overview("day", now=now)
                self.assertEqual(day["summary"]["calls"], 1)
                self.assertEqual(day["summary"]["total_tokens"], 140)
                self.assertEqual(len(day["series"]), 24)
                self.assertEqual(day["series"][10]["total_tokens"], 140)
                self.assertEqual(day["history"][0]["by_model"][0]["model"], "provider/model")
                self.assertNotIn("secret_prompt", day["history"][0]["by_model"][0])
                week = usage_history.get_overview("week", now=now)
                self.assertEqual(week["summary"]["calls"], 2)
                self.assertEqual(week["summary"]["measured_calls"], 1)
                self.assertEqual(week["summary"]["estimated_cost_usd"], 0.00056)
                self.assertEqual({item["route"] for item in week["by_route"]}, {"general", "writing"})
                self.assertEqual(len(week["series"]), 3)
                month = usage_history.get_overview("month", now=now)
                self.assertEqual(month["summary"]["calls"], 2)
                self.assertEqual(month["timezone"], "Asia/Ho_Chi_Minh")

                self.assertNotIn(b"DO NOT STORE", path.read_bytes())
                usage_history.init_usage_db()  # May restart without losing events.
                self.assertEqual(usage_history.get_overview("week", now=now)["summary"]["calls"], 2)

    def test_invalid_metrics_are_missing_not_misrepresented_as_zero(self):
        with TemporaryDirectory() as folder:
            with patch.object(usage_history, "DB_PATH", Path(folder) / "usage.db"):
                usage_history.init_usage_db()
                usage_history.record_usage({
                    "route": "research", "usage_available": True,
                    "total_tokens": -99, "input_tokens": float("nan"),
                    "estimated_cost_usd": float("inf"), "duration_ms": -2,
                    "by_model": [],
                })
                with usage_history._db() as connection:
                    row = connection.execute("SELECT * FROM ai_usage_events").fetchone()
                self.assertIsNone(row["total_tokens"])
                self.assertIsNone(row["estimated_cost_usd"])
                self.assertIsNone(row["duration_ms"])

    def test_best_effort_tracking_never_breaks_ai_response(self):
        with TemporaryDirectory() as folder:
            with patch.object(usage_history, "DB_PATH", Path(folder) / "nonexistent" / "usage.db"):
                with patch.object(usage_history.logger, "error") as log_error:
                    self.assertIsNone(usage_history.record_usage_safely({"route": "writing"}))
                    self.assertTrue(log_error.called)


if __name__ == "__main__":
    unittest.main()
