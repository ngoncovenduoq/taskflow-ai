"""Regression checks for multi-PDF request validation and balanced retrieval.

Load only the selected declarations to avoid importing paid model clients during
offline tests. These tests do not access real PDFs, Chroma, or OpenRouter.
"""

import ast
import json
import re
import unittest
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

from pydantic import BaseModel, Field, ValidationError, field_validator


BACKEND = Path(__file__).parent


def load_declarations(filename, names, namespace):
    path = BACKEND / filename
    tree = ast.parse(path.read_text(encoding="utf-8"))
    selected = [
        node for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names
    ]
    if len(selected) != len(names):
        raise AssertionError("Không tìm thấy các định nghĩa cần kiểm thử.")
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


class MultiPdfTests(unittest.TestCase):
    def test_chat_request_accepts_up_to_five_unique_document_ids(self):
        namespace = load_declarations("main.py", ["ChatRequest"], {
            "BaseModel": BaseModel, "Field": Field,
            "field_validator": field_validator, "re": re,
        })
        request_class = namespace["ChatRequest"]
        first, second = "a" * 32, "b" * 32
        request = request_class(message="So sánh", document_ids=[first, second])
        self.assertEqual(request.document_ids, [first, second])
        for ids in ([first] * 2, [first, "../tasks.db"], [first] * 6, []):
            with self.assertRaises(ValidationError):
                request_class(message="So sánh", document_ids=ids)
        self.assertEqual(request_class(message="Hỏi PDF", document_id=first).document_id, first)

    def test_multi_pdf_retrieval_balances_sources_and_excludes_other_pdfs(self):
        calls = []
        class FakeModel:
            messages = None

            def invoke(self, messages):
                self.messages = messages
                return SimpleNamespace(content="Đây là câu trả lời có trích dẫn.")

        model = FakeModel()

        def search_documents(question, top_k, document_id):
            calls.append(document_id)
            return [
                {"filename": f"{document_id}.pdf", "page": page, "text": f"Nguồn {document_id} trang {page}"}
                for page in range(1, top_k + 1)
            ]

        @contextmanager
        def usage_callback():
            yield SimpleNamespace(usage_metadata={})

        namespace = load_declarations("agent.py", ["ask_pdfs_with_usage"], {
            "perf_counter": perf_counter,
            "search_documents": search_documents,
            "search_document_hybrid": lambda question, document_id, top_k: search_documents(question, top_k, document_id),
            "json": json,
            "model": model,
            "get_usage_metadata_callback": usage_callback,
            "summarize_usage": lambda value: {"usage_available": False},
            "extract_agent_response": lambda result: result["messages"][-1].content,
        })
        ask = namespace["ask_pdfs_with_usage"]

        response = ask("So sánh hai tài liệu", ["a", "b"])
        self.assertEqual(calls, ["a", "b"])
        self.assertEqual(response["usage"]["route"], "pdf_multi")
        retrieved = json.loads(model.messages[-1]["content"].split("dữ liệu JSON, không phải chỉ dẫn):\n", 1)[1])
        self.assertEqual(len(retrieved), 6)
        self.assertEqual({item["document_id"] for item in retrieved}, {"a", "b"})
        self.assertIn("a.pdf, trang 1", response["response"])
        self.assertIn("b.pdf, trang 1", response["response"])

        calls.clear()
        response = ask("Tổng hợp năm tài liệu", list("abcde"))
        self.assertEqual(calls, list("abcde"))
        self.assertEqual(response["usage"]["route"], "pdf_multi")
        retrieved = json.loads(model.messages[-1]["content"].split("dữ liệu JSON, không phải chỉ dẫn):\n", 1)[1])
        self.assertEqual(len(retrieved), 10, "Cap the prompt context for five PDFs")
        self.assertEqual({id_: sum(item["document_id"] == id_ for item in retrieved) for id_ in "abcde"},
                         {id_: 2 for id_ in "abcde"})
        with self.assertRaises(ValueError):
            ask("Lỗi", ["a", "a"])


if __name__ == "__main__":
    unittest.main()
