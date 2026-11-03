"""Direct SQLite task management routes; these endpoints never invoke an LLM.

This router reuses the database functions already used by TaskFlow's agent.
"""

import logging

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from database import (
    add_task,
    get_tasks,
    complete_task as db_complete_task,
    delete_task as db_delete_task,
)
from task_summary import COMPLETED_STATUSES


router = APIRouter(prefix="/api/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)


class NewTask(BaseModel):
    title: str = Field(min_length=1, max_length=200)


@router.get("/")
def list_task_items() -> dict:
    """List persisted tasks without calling the AI model."""

    try:
        rows = get_tasks()
        tasks = [
            {
                "id": int(task_id),
                "title": str(title),
                "status": str(status),
                "completed": str(status).strip().casefold() in COMPLETED_STATUSES,
            }
            for task_id, title, status in rows
        ]
        return {"tasks": tasks}
    except Exception as error:
        logger.exception("Unable to list tasks")
        raise HTTPException(status_code=500, detail="Không thể tải danh sách công việc.") from error


@router.post("/", status_code=201)
def create_task_item(payload: NewTask) -> dict:
    """Create one task in the same SQLite database used by the chat agent."""

    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Tên công việc không được để trống.")

    try:
        task_id = add_task(title)
        return {"id": int(task_id), "title": title, "status": "pending", "completed": False}
    except Exception as error:
        logger.exception("Unable to create task")
        raise HTTPException(status_code=500, detail="Không thể tạo công việc.") from error


@router.patch("/{task_id}/complete")
def complete_task_item(task_id: int = Path(gt=0)) -> dict:
    """Mark the explicitly selected task as completed."""

    try:
        success = db_complete_task(task_id)
    except Exception as error:
        logger.exception("Unable to complete task")
        raise HTTPException(status_code=500, detail="Không thể hoàn thành công việc.") from error

    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc cần hoàn thành.")

    return {"id": task_id, "status": "completed", "completed": True}


@router.delete("/{task_id}")
def delete_task_item(task_id: int = Path(gt=0)) -> dict:
    """Delete only the task whose ID the user explicitly selected."""

    try:
        success = db_delete_task(task_id)
    except Exception as error:
        logger.exception("Unable to delete task")
        raise HTTPException(status_code=500, detail="Không thể xóa công việc.") from error

    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc cần xóa.")

    return {"id": task_id, "deleted": True}
