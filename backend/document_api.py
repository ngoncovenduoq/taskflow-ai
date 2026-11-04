
import json
import logging
import re
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pypdf import PdfReader
from starlette.concurrency import run_in_threadpool

from rag_store import delete_document, get_document, index_document, list_documents


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)
logger = logging.getLogger(__name__)

# Thu muc luu noi dung tai lieu
DATA_DIR = Path(__file__).parent / "data" / "documents"

# Gioi han file PDF 5 MB
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF and extract text from its pages."""

    filename = Path((file.filename or "").replace("\\", "/")).name[:180]

    # Kiem tra duoi file
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Chi chap nhan file PDF."
        )

    # Doc file voi gioi han kich thuoc
    contents = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File vuot qua 5 MB."
        )

    # Kiem tra file co dinh dang PDF hay khong
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="File khong phai PDF hop le."
        )

    # Doc va trich xuat noi dung
    try:
        reader = PdfReader(BytesIO(contents))

        pages = []

        for index, page in enumerate(reader.pages):
            text = page.extract_text() or ""

            pages.append({
                "page": index + 1,
                "text": text
            })

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Khong the doc file PDF."
        )

    full_text = "\n".join(
        page["text"] for page in pages
    )

    if not full_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Khong tim thay van ban. PDF co the la ban scan."
        )

    # Tao ma dinh danh cho tai lieu
    document_id = uuid4().hex

    document_data = {
        "document_id": document_id,
        "filename": filename,
        "pages": pages
    }

    # Luu noi dung de su dung cho RAG sau nay
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    save_path = DATA_DIR / f"{document_id}.json"

    save_path.write_text(
        json.dumps(
            document_data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    # Index immediately, so an uploaded document is actually usable in chat.
    # If indexing fails, keep the JSON and allow the user to retry.
    try:
        chunk_count = await run_in_threadpool(index_document, document_id)
    except Exception as error:
        logger.error("PDF indexing failed: type=%s", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="Đã lưu nội dung PDF nhưng chưa thể lập chỉ mục. Hãy bấm 'Thử lại'.",
        ) from error

    return {
        "message": "PDF uploaded successfully",
        "document_id": document_id,
        "filename": filename,
        "total_pages": len(pages),
        "total_characters": len(full_text),
        "preview": full_text[:500],
        "chunk_count": chunk_count,
        "indexed": True,
    }


@router.get("/")
def get_document_list():
    try:
        return {"documents": list_documents()}
    except Exception as error:
        logger.error("PDF list failed: type=%s", type(error).__name__)
        raise HTTPException(status_code=503, detail="Không thể tải danh sách tài liệu.") from error


def _validate_id(document_id: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{32}", document_id):
        raise HTTPException(status_code=422, detail="ID tài liệu không hợp lệ.")


@router.post("/{document_id}/index")
def retry_document_index(document_id: str):
    _validate_id(document_id)
    if get_document(document_id) is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
    try:
        return {"document_id": document_id, "chunk_count": index_document(document_id), "indexed": True}
    except Exception as error:
        logger.error("PDF reindex failed: type=%s", type(error).__name__)
        raise HTTPException(status_code=503, detail="Không thể lập chỉ mục PDF.") from error


@router.delete("/{document_id}")
def delete_document_item(document_id: str):
    _validate_id(document_id)
    try:
        deleted = delete_document(document_id)
    except Exception as error:
        logger.error("PDF delete failed: type=%s", type(error).__name__)
        raise HTTPException(status_code=503, detail="Không thể xóa tài liệu.") from error
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
    return {"document_id": document_id, "deleted": True}
