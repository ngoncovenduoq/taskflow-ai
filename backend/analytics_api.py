"""Read-only AI usage analytics API; no external model calls."""

import logging
import sqlite3
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from usage_history import get_overview, init_usage_db


router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)
init_usage_db()


@router.get("/overview")
def analytics_overview(period: Literal["day", "week", "month"] = Query("week")):
    try:
        return get_overview(period)
    except sqlite3.Error as error:
        logger.error("Unable to load analytics: type=%s", type(error).__name__)
        raise HTTPException(status_code=500, detail="Không tải được thống kê AI từ SQLite.") from error
