
import json
from pathlib import Path

import chromadb


# 1. Duong dan luu du lieu
BASE_DIR = Path(__file__).parent

DOCUMENTS_DIR = BASE_DIR / "data" / "documents"

VECTOR_DB_DIR = BASE_DIR / "chroma_db"


# 2. Khoi tao Vector Database
client = chromadb.PersistentClient(
    path=str(VECTOR_DB_DIR)
)

collection = client.get_or_create_collection(
    name="taskflow_documents"
)


# 3. Chia van ban thanh cac doan nho
def split_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 120
) -> list[str]:

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


# 4. Doc cac file JSON va tao embeddings
def index_documents() -> int:

    if not DOCUMENTS_DIR.exists():
        print("Chua co thu muc documents.")
        return 0

    total_chunks = 0

    for file_path in DOCUMENTS_DIR.glob("*.json"):

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        document_id = data["document_id"]
        filename = data["filename"]

        ids = []
        documents = []
        metadatas = []

        for page_data in data["pages"]:

            page_number = page_data["page"]
            page_text = page_data["text"]

            chunks = split_text(page_text)

            for index, chunk in enumerate(chunks):

                chunk_id = (
                    f"{document_id}_"
                    f"{page_number}_{index}"
                )

                ids.append(chunk_id)
                documents.append(chunk)

                metadatas.append({
                    "document_id": document_id,
                    "filename": filename,
                    "page": page_number
                })

        # Luu theo batch de xu ly tai lieu dai
        batch_size = 50

        for start in range(0, len(ids), batch_size):

            end = start + batch_size

            collection.upsert(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end]
            )

        total_chunks += len(ids)

        print(
            f"Da xu ly {filename}: "
            f"{len(ids)} chunks"
        )

    return total_chunks


# 5. Tim kiem noi dung lien quan
def search_documents(
    question: str,
    top_k: int = 3
) -> list[dict]:

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas"]
    )

    output = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    for text, metadata in zip(documents, metadatas):

        output.append({
            "filename": metadata["filename"],
            "page": metadata["page"],
            "text": text
        })

    return output


# 6. Kiem thu truc tiep
if __name__ == "__main__":

    print("Dang tao chi muc tai lieu...")

    total = index_documents()

    print(f"Da xu ly {total} chunks.")
    print(f"So chunks trong ChromaDB: {collection.count()}")

    if collection.count() > 0:

        question = input(
            "\nNhap cau hoi ve tai lieu: "
        )

        results = search_documents(question)

        for index, item in enumerate(results, start=1):

            print(f"\n--- Ket qua {index} ---")

            print("File:", item["filename"])
            print("Trang:", item["page"])
            print("Noi dung:")
            print(item["text"])
