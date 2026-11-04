"""Direct SQLite task management routes; these endpoints never invoke an LLM.

This router reuses the database functions already used by TaskFlow's agent.
"""

import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from database import (
    add_task,
    get_tasks_detailed,
    update_task as db_update_task,
    complete_task as db_complete_task,
    reopen_task as db_reopen_task,
    delete_task as db_delete_task,
)
from task_summary import COMPLETED_STATUSES


router = APIRouter(prefix="/api/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)


class NewTask(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: str = "medium"
    due_date: str | None = None


def _validated_fields(payload: NewTask) -> tuple[str, str, str | None]:
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Tên công việc không được để trống.")
    if payload.priority not in {"low", "medium", "high"}:
        raise HTTPException(status_code=422, detail="Độ ưu tiên phải là low, medium hoặc high.")
    if payload.due_date is not None:
        if len(payload.due_date) != 10:
            raise HTTPException(status_code=422, detail="Hạn hoàn thành phải có dạng YYYY-MM-DD.")
        try:
            date.fromisoformat(payload.due_date)
        except ValueError as error:
            raise HTTPException(status_code=422, detail="Hạn hoàn thành không hợp lệ.") from error
    return title, payload.priority, payload.due_date


@router.get("/")
def list_task_items() -> dict:
    """List persisted tasks without calling the AI model."""

    try:
        rows = get_tasks_detailed()
        tasks = [
            {
                "id": int(task_id),
                "title": str(title),
                "status": str(status),
                "completed": str(status).strip().casefold() in COMPLETED_STATUSES,
                "priority": str(priority),
                "due_date": due_date,
            }
            for task_id, title, status, priority, due_date in rows
        ]
        return {"tasks": tasks}
    except Exception as error:
        logger.exception("Unable to list tasks")
        raise HTTPException(status_code=500, detail="Không thể tải danh sách công việc.") from error


@router.post("/", status_code=201)
def create_task_item(payload: NewTask) -> dict:
    """Create one task in the same SQLite database used by the chat agent."""

    title, priority, due_date = _validated_fields(payload)

    try:
        task_id = add_task(title, priority, due_date)
        return {
            "id": int(task_id), "title": title, "status": "pending",
            "completed": False, "priority": priority, "due_date": due_date,
        }
    except Exception as error:
        logger.exception("Unable to create task")
        raise HTTPException(status_code=500, detail="Không thể tạo công việc.") from error


@router.put("/{task_id}")
def update_task_item(payload: NewTask, task_id: int = Path(gt=0)) -> dict:
    """Edit a task while retaining its ID and completion status."""

    title, priority, due_date = _validated_fields(payload)
    try:
        success = db_update_task(task_id, title, priority, due_date)
    except Exception as error:
        logger.exception("Unable to update task")
        raise HTTPException(status_code=500, detail="Không thể chỉnh sửa công việc.") from error

    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc cần sửa.")
    return {"id": task_id, "updated": True}


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


@router.patch("/{task_id}/reopen")
def reopen_task_item(task_id: int = Path(gt=0)) -> dict:
    """Undo completion and put an existing task back in pending status."""

    try:
        success = db_reopen_task(task_id)
    except Exception as error:
        logger.exception("Unable to reopen task")
        raise HTTPException(status_code=500, detail="Không thể mở lại công việc.") from error

    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc cần mở lại.")
    return {"id": task_id, "status": "pending", "completed": False}


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
