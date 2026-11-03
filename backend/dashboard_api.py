"""Read-only dashboard summary API for the existing TaskFlow SQLite DB."""

import logging

from fastapi import APIRouter, HTTPException

from database import get_tasks
from task_summary import summarize_tasks


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)


@router.get("/summary")
def get_dashboard_summary() -> dict:
    """Return aggregate task counts without consuming OpenRouter tokens."""

    try:
        return summarize_tasks(get_tasks())
    except Exception as error:
        logger.error("Dashboard summary failed: type=%s", type(error).__name__)
        raise HTTPException(
            status_code=500,
            detail="Không thể tải thống kê công việc.",
        ) from error
