"""SQLite tracking for AI token usage and estimated cost, without prompts."""

import json
import logging
import math
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


DB_PATH = Path(__file__).with_name("usage_history.db")
# Viet Nam has no daylight-saving changes; this also works on Windows without tzdata.
LOCAL_TZ = timezone(timedelta(hours=7), name="Asia/Ho_Chi_Minh")
logger = logging.getLogger(__name__)


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


def init_usage_db():
    with _db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                route TEXT NOT NULL,
                usage_available INTEGER NOT NULL,
                total_tokens INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                reasoning_tokens INTEGER,
                estimated_cost_usd REAL,
                duration_ms REAL,
                models_json TEXT NOT NULL
            )
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_created ON ai_usage_events(created_at)")


def _tokens(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return int(value) if 0 <= value <= 1_000_000_000 else None


def _nonnegative_float(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value) if 0 <= value <= 1_000_000 else None


def record_usage(usage: dict | None) -> int | None:
    """Record one model-backed request; never store question or response content."""
    if not isinstance(usage, dict) or usage.get("route") in {"local_memory", "local"}:
        return None
    route = str(usage.get("route") or "unknown")[:40]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", route):
        route = "unknown"
    measured = usage.get("usage_available") is True
    models = []
    for model in usage.get("by_model") or []:
        if not isinstance(model, dict) or len(models) >= 10:
            break
        models.append({
            "model": str(model.get("model") or "unknown")[:140],
            "total_tokens": _tokens(model.get("total_tokens")),
            "estimated_cost_usd": _nonnegative_float(model.get("estimated_cost_usd")),
        })
    with _db() as connection:
        cursor = connection.execute("""
            INSERT INTO ai_usage_events
              (created_at, route, usage_available, total_tokens, input_tokens,
               output_tokens, reasoning_tokens, estimated_cost_usd, duration_ms, models_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(timespec="seconds"), route, int(measured),
            _tokens(usage.get("total_tokens")) if measured else None,
            _tokens(usage.get("input_tokens")) if measured else None,
            _tokens(usage.get("output_tokens")) if measured else None,
            _tokens(usage.get("reasoning_tokens")) if measured else None,
            _nonnegative_float(usage.get("estimated_cost_usd")),
            _nonnegative_float(usage.get("duration_ms")),
            json.dumps(models, ensure_ascii=False),
        ))
        return int(cursor.lastrowid)


def record_usage_safely(usage: dict | None):
    """Analytics must never prevent the user's AI response from being delivered."""
    try:
        return record_usage(usage)
    except (sqlite3.Error, OSError, TypeError, ValueError) as error:
        logger.error("Usage event not saved: type=%s", type(error).__name__)
        return None


def _start_of_period(period: str, now: datetime):
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "day":
        return today
    if period == "week":
        return today - timedelta(days=today.weekday())
    if period == "month":
        return today.replace(day=1)
    raise ValueError("Unsupported analytics period")


def _aggregate(rows):
    costs = [row["estimated_cost_usd"] for row in rows if row["estimated_cost_usd"] is not None]
    return {
        "calls": len(rows),
        "measured_calls": sum(row["usage_available"] for row in rows),
        "total_tokens": sum(row["total_tokens"] or 0 for row in rows),
        "input_tokens": sum(row["input_tokens"] or 0 for row in rows),
        "output_tokens": sum(row["output_tokens"] or 0 for row in rows),
        "reasoning_tokens": sum(row["reasoning_tokens"] or 0 for row in rows),
        "estimated_cost_usd": round(sum(costs), 8) if costs else None,
    }


def get_overview(period: str = "week", now: datetime | None = None) -> dict:
    current = (now or datetime.now(LOCAL_TZ)).astimezone(LOCAL_TZ)
    start = _start_of_period(period, current)
    start_utc = start.astimezone(timezone.utc).isoformat(timespec="seconds")
    current_utc = current.astimezone(timezone.utc).isoformat(timespec="seconds")
    with _db() as connection:
        records = connection.execute(
            "SELECT * FROM ai_usage_events WHERE created_at >= ? AND created_at <= ? ORDER BY id DESC",
            (start_utc, current_utc),
        ).fetchall()
    rows = [dict(row) for row in records]
    totals = _aggregate(rows)

    by_route = {}
    by_slot = {}
    for row in rows:
        route = row["route"]
        by_route.setdefault(route, []).append(row)
        local_created = datetime.fromisoformat(row["created_at"]).astimezone(LOCAL_TZ)
        slot = local_created.strftime("%H") if period == "day" else local_created.strftime("%Y-%m-%d")
        by_slot.setdefault(slot, []).append(row)

    series = []
    if period == "day":
        slots = [(f"{hour:02d}", f"{hour:02d}:00") for hour in range(24)]
    else:
        days = (current.date() - start.date()).days + 1
        slots = [((start + timedelta(days=i)).strftime("%Y-%m-%d"),
                  (start + timedelta(days=i)).strftime("%d/%m")) for i in range(days)]
    for key, label in slots:
        series.append({"label": label, **_aggregate(by_slot.get(key, []))})

    history = []
    for row in rows[:40]:
        history.append({
            "id": row["id"], "created_at": row["created_at"], "route": row["route"],
            "usage_available": bool(row["usage_available"]),
            "total_tokens": row["total_tokens"], "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"], "reasoning_tokens": row["reasoning_tokens"],
            "estimated_cost_usd": row["estimated_cost_usd"],
            "duration_ms": row["duration_ms"],
            "by_model": json.loads(row["models_json"]),
        })
    return {
        "period": period, "timezone": "Asia/Ho_Chi_Minh", "summary": totals,
        "by_route": [{"route": route, **_aggregate(group)} for route, group in
                     sorted(by_route.items(), key=lambda item: len(item[1]), reverse=True)],
        "series": series, "history": history,
    }
