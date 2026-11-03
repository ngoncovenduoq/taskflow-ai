import os

from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv()


def search_web(query: str) -> list[dict]:
    """Search the web and return relevant results."""

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise ValueError("TAVILY_API_KEY is missing.")

    client = TavilyClient(api_key=api_key)

    response = client.search(
        query=query,
        search_depth="basic",
        max_results=3,
        include_answer=False
    )

    results = []

    for item in response.get("results", []):

        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", "")[:350]
        })

    return results


if __name__ == "__main__":

    print("Testing Research Search...")

    results = search_web(
        "What is Retrieval Augmented Generation in AI?"
    )

    for index, item in enumerate(results, start=1):

        print(f"\nResult {index}")
        print("Title:", item["title"])
        print("URL:", item["url"])
        print("Content:", item["content"])