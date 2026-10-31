
import os

from dotenv import load_dotenv
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI


# 1. Doc API key tu file .env
load_dotenv()


# 2. Danh sach luu cong viec
tasks = []


# 3. Tool tao cong viec
@tool
def create_task(title: str) -> str:
    """Create a new task with the given title."""

    task = {
        "id": len(tasks) + 1,
        "title": title,
        "status": "pending"
    }

    tasks.append(task)

    return f"Task created successfully: {task}"


# 4. Tool xem danh sach cong viec
@tool
def list_tasks() -> str:
    """Get all existing tasks."""

    if not tasks:
        return "No tasks found."

    return str(tasks)


# 5. Ket noi voi LLM
model = ChatGoogleGenerativeAI(
    model=os.getenv("GOOGLE_MODEL", "gemini-3.8-flash")
)


# 6. Tao AI Agent
agent = create_agent(
    model=model,
    tools=[create_task, list_tasks],
    system_prompt=(
        "You are TaskFlow AI, a helpful task assistant. "
        "When users ask to create tasks, use create_task. "
        "When users ask to see tasks, use list_tasks. "
        "Never claim a task was created unless the tool "
        "confirms success. "
        "Reply in the same language as the user."
    )
)


# 7. Ham de main.py goi AI Agent

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

    # Truong hop Gemini tra ve danh sach
    if isinstance(content, list):
        texts = []

        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))

        return "\n".join(texts).strip()

    return str(content)
