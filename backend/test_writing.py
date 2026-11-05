"""Offline regression tests for SQLite drafts, request limits and exports."""

import ast
from io import BytesIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import Literal
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from pydantic import BaseModel, Field, ValidationError, field_validator


BACKEND = Path(__file__).parent
sys.path.insert(0, str(BACKEND))
import writing_store  # noqa: E402
from writing_export import export_docx, export_pdf, export_txt  # noqa: E402


class WritingTests(unittest.TestCase):
    def test_store_create_edit_history_delete(self):
        with TemporaryDirectory() as folder:
            with patch.object(writing_store, "DB_PATH", Path(folder) / "drafts.db"):
                writing_store.init_writing_db()
                first = writing_store.create_draft("Email A", "email", "professional", "Hỏi việc", "Xin chào")
                second = writing_store.create_draft("Báo cáo B", "report", "academic", "Báo cáo", "Nội dung B")
                self.assertEqual([item["id"] for item in writing_store.list_drafts()], [second["id"], first["id"]])
                self.assertNotIn("content", writing_store.list_drafts()[0], "History should fetch only metadata")
                self.assertEqual(writing_store.get_draft(first["id"])["content"], "Xin chào")
                updated = writing_store.update_draft(first["id"], "Email đã sửa", "Xin chào Quân", "friendly")
                self.assertEqual(updated["title"], "Email đã sửa")
                self.assertEqual(updated["content"], "Xin chào Quân")
                self.assertEqual(updated["tone"], "friendly")
                self.assertIsNone(writing_store.update_draft(9999, "Mất", "Nội dung", "neutral"))
                self.assertTrue(writing_store.delete_draft(second["id"]))
                self.assertFalse(writing_store.delete_draft(second["id"]))
                self.assertIsNone(writing_store.get_draft(second["id"]))
                writing_store.init_writing_db()
                self.assertEqual(len(writing_store.list_drafts()), 1)

    def test_request_validation(self):
        path = BACKEND / "writing_api.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {"GenerateRequest", "SaveRequest", "ReviseRequest"}
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name in names]
        namespace = {
            "BaseModel": BaseModel, "Field": Field, "field_validator": field_validator,
            "Kind": Literal["email", "report", "essay", "cv", "custom"],
            "Tone": Literal["professional", "academic", "friendly", "neutral"],
            "Action": Literal["rewrite", "shorten", "expand", "proofread"],
        }
        exec(compile(ast.Module(body=classes, type_ignores=[]), str(path), "exec"), namespace)
        generate = namespace["GenerateRequest"]
        self.assertEqual(generate(instructions="  Viết email  ").instructions, "Viết email")
        for bad in ["  a  ", "a" * 4001]:
            with self.assertRaises(ValidationError):
                generate(instructions=bad)
        with self.assertRaises(ValidationError):
            generate(instructions="Viết email", kind="unsupported")
        save = namespace["SaveRequest"]
        with self.assertRaises(ValidationError):
            save(title="   ", content="Nội dung")
        revise = namespace["ReviseRequest"]
        with self.assertRaises(ValidationError):
            revise(title="Bản thảo", content="   ", action="rewrite")
        with self.assertRaises(ValidationError):
            revise(title="Bản thảo", content="Nội dung", action="delete")

    def test_export_formats_preserve_vietnamese_text(self):
        title = "Thư ứng tuyển lập trình viên"
        content = "Kính gửi Quý công ty,\n\n# Giới thiệu\nTôi đang học xử lý ngôn ngữ tự nhiên.\n- Python và PyTorch"
        txt = export_txt(title, content)
        self.assertTrue(txt.startswith(b"\xef\xbb\xbf"))
        self.assertIn("ngôn ngữ tự nhiên", txt.decode("utf-8-sig"))

        from docx import Document
        docx = export_docx(title, content)
        with ZipFile(BytesIO(docx)) as archive:
            self.assertIn("word/document.xml", archive.namelist())
        document = Document(BytesIO(docx))
        words = " ".join(paragraph.text for paragraph in document.paragraphs)
        self.assertIn(title, words)
        self.assertIn("ngôn ngữ tự nhiên", words)

        from pypdf import PdfReader
        pdf = export_pdf(title, content)
        self.assertTrue(pdf.startswith(b"%PDF-"))
        reader = PdfReader(BytesIO(pdf))
        self.assertGreaterEqual(len(reader.pages), 1)
        extracted = " ".join(page.extract_text() for page in reader.pages)
        self.assertIn("Giới thiệu", extracted)
        self.assertIn("ngôn ngữ tự nhiên", extracted)


if __name__ == "__main__":
    unittest.main()
