import os

from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter


# 1. Load API key
load_dotenv()


# 2. Khoi tao LLM
model = ChatOpenRouter(
    model=os.getenv(
        "WRITING_MODEL",
        "openai/gpt-oss-120b"
    ),
    max_tokens=700,
    reasoning={"effort": "low"},
    max_retries=1
)


# 3. System prompt
WRITING_PROMPT = """
You are the Writing Agent of TaskFlow AI.

Your job is to create and improve written content.

Capabilities:
- Write professional emails.
- Write articles and blog posts.
- Write short reports.
- Summarize text.
- Rewrite text in different styles.

Rules:
1. Follow the user's instructions carefully.
2. Always respond in the user's language.
3. Write clear, natural, and well-structured content.
4. Adapt the tone to the user's request.
5. Never invent facts, experiences, achievements, or qualifications.
6. Only mention skills and experience explicitly provided by the user.
7. Do not exaggerate the user's abilities.
8. If information is missing, use appropriate placeholders.
9. Never invent citations, sources, or website URLs.
10. Return the finished content without unnecessary explanations.

For job application emails:
- Maintain a professional and polite tone.
- Do not claim practical experience unless the user provides it.
- Do not claim expertise when the user only mentions basic knowledge.
- Use placeholders for missing personal information.
- Never mention projects, work experience, internships, or achievements unless explicitly provided in the user's request or supplied reference material.
"""


# 4. Ham tao noi dung
def write_content(request: str) -> str:
    """Generate written content based on user instructions."""

    print(f"[WRITING AGENT] Writing: {request}")

    response = model.invoke([
        ("system", WRITING_PROMPT),
        ("human", request)
    ])

    content = response.content

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):

        texts = []

        for block in content:

            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))

        return "\n".join(texts).strip()

    return str(content)


# 5. Test Writing Agent
if __name__ == "__main__":

    print("Testing Writing Agent...\n")

    result = write_content(
        "Viết email ứng tuyển vị trí AI Engineer Intern "
        "bằng tiếng Việt, khoảng 120 từ. "
        "Ứng viên tốt nghiệp ngành Khoa học máy tính, "
        "có kiến thức Python và Machine Learning. "
        "Giọng văn chuyên nghiệp. "
        "Không tự bịa kinh nghiệm hoặc thành tích. "
        "Sử dụng [Tên công ty] nếu cần."
    )

    print("\n--- Writing Result ---\n")
    print(result)