"""Pure helpers for TaskFlow AI dashboard statistics.

The existing database.get_tasks() returns tuples of
(task_id, title, status). No AI/model calls are made here.
"""

from collections.abc import Iterable


COMPLETED_STATUSES = frozenset({
    "completed",
    "complete",
    "done",
    "finished",
    "hoàn thành",
    "hoan thanh",
})


def summarize_tasks(tasks: Iterable[tuple[int, str, str]]) -> dict:
    """Return real task counts and completion rate from database rows.

    Every task not explicitly marked completed is counted as unfinished.
    This matches the current pending/completed SQLite workflow and avoids
    incorrectly treating pending tasks as already in progress.
    """

    total = 0
    completed = 0

    for _task_id, _title, status in tasks:
        total += 1
        normalized = str(status).strip().casefold()
        if normalized in COMPLETED_STATUSES:
            completed += 1

    unfinished = total - completed

    return {
        "total_tasks": total,
        "unfinished_tasks": unfinished,
        "completed_tasks": completed,
        "completion_percent": round(completed / total * 100, 1) if total else 0.0,
        "has_tasks": total > 0,
    }
