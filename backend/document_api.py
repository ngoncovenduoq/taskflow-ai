
import json
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pypdf import PdfReader


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

# Thu muc luu noi dung tai lieu
DATA_DIR = Path(__file__).parent / "data" / "documents"

# Gioi han file PDF 5 MB
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF and extract text from its pages."""

    filename = Path(file.filename or "").name

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

    return {
        "message": "PDF uploaded successfully",
        "document_id": document_id,
        "filename": filename,
        "total_pages": len(pages),
        "total_characters": len(full_text),
        "preview": full_text[:500]
    }
