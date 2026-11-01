
import os

from dotenv import load_dotenv
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_groq import ChatGroq

from database import (
    init_db,
    add_task,
    get_tasks,
    complete_task as db_complete_task,
    delete_task as db_delete_task
)


# 1. Doc API key tu file .env
load_dotenv()


# 2. Khoi tao SQLite database
init_db()


# 3. Tool tao cong viec
@tool
def create_task(title: str) -> str:
    """Create a new task and save it to the database."""

    task_id = add_task(title)

    return (
        f"Task created successfully. "
        f"ID: {task_id}, Title: {title}"
    )


# 4. Tool xem danh sach cong viec
@tool
def list_tasks() -> str:
    """Get all tasks from the database."""

    tasks = get_tasks()

    if not tasks:
        return "No tasks found."

    result = []

    for task_id, title, status in tasks:
        result.append(
            f"ID: {task_id}, "
            f"Title: {title}, "
            f"Status: {status}"
        )

    return "\n".join(result)


# 5. Tool danh dau cong viec hoan thanh
@tool
def mark_task_completed(task_id: int) -> str:
    """Mark an existing task as completed by its ID."""

    success = db_complete_task(task_id)

    if success:
        return f"Task {task_id} completed successfully."

    return f"Task {task_id} not found."


# 6. Tool xoa cong viec
@tool
def remove_task(task_id: int) -> str:
    """Delete a task by ID when the user explicitly requests it."""

    success = db_delete_task(task_id)

    if success:
        return f"Task {task_id} deleted successfully."

    return f"Task {task_id} not found."


# 7. Ket noi voi Groq LLM
model = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
)


# 8. Tao AI Agent
agent = create_agent(
    model=model,
    tools=[
        create_task,
        list_tasks,
        mark_task_completed,
        remove_task
    ],
    system_prompt=(
        "You are TaskFlow AI, a task management assistant. "
        "Help users create, list, complete, and delete tasks. "
        "Always use the appropriate tool for task operations. "
        "Never claim an operation succeeded unless its tool confirms it. "
        "Only delete tasks when the user explicitly requests deletion. "
        "Ask for clarification if a task ID is missing or ambiguous. "
        "Respond in the user's language."
    )
)


# 9. Ham de main.py goi AI Agent
def ask_agent(message: str) -> str:

    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ]
    })

    # Lay noi dung phan hoi cuoi cung
    content = result["messages"][-1].content

    # Truong hop phan hoi la chuoi
    if isinstance(content, str):
        return content

    # Truong hop phan hoi la danh sach
    if isinstance(content, list):
        texts = []

        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))

        return "\n".join(texts).strip()

    return str(content)
