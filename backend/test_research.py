"""Offline tests for the Research workspace's persistence and source safety."""

import ast
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError, field_validator


BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))
import research_store  # noqa: E402


class ResearchTests(unittest.TestCase):
    def test_query_validation_and_trimming(self):
        path = BACKEND_DIR / "research_api.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        node = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ResearchRequest")
        namespace = {"BaseModel": BaseModel, "Field": Field, "field_validator": field_validator}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
        request = namespace["ResearchRequest"]
        self.assertEqual(request(query="  RAG  ").query, "RAG")
        for invalid in ["  x  ", "a" * 401, "    "]:
            with self.assertRaises(ValidationError):
                request(query=invalid)

    def test_history_roundtrip_and_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "research.db"
            with patch.object(research_store, "DB_PATH", db_path):
                research_store.init_research_db()
                first = research_store.save_research(
                    "Tìm hiểu RAG", "## Tổng hợp", [{"title": "Nguồn A", "url": "https://example.org"}],
                )
                second = research_store.save_research("Học NLP", "Nội dung", [])
                self.assertTrue(db_path.is_file())
                self.assertEqual([item["id"] for item in research_store.list_research()], [second["id"], first["id"]])
                self.assertEqual(research_store.list_research()[-1]["sources"], first["sources"])
                self.assertEqual(len(research_store.list_research(limit=1)), 1)
                self.assertTrue(research_store.delete_research(first["id"]))
                self.assertFalse(research_store.delete_research(first["id"]))
                self.assertEqual([item["id"] for item in research_store.list_research()], [second["id"]])
                research_store.init_research_db()  # Idempotent across restarts.

    def test_source_normalization_rejects_unsafe_and_duplicate_urls(self):
        path = BACKEND_DIR / "research_api.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "normalize_sources")
        namespace = {"urlparse": urlparse}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
        normalize = namespace["normalize_sources"]
        results = [
            {"title": "Đáng tin", "url": "https://example.org/research", "content": "Một đoạn ngắn"},
            {"title": "Trùng", "url": "https://example.org/research"},
            {"title": "Unsafe", "url": "javascript:alert(1)"},
            {"title": "Local", "url": "file:///private"},
            {"title": "Có userinfo", "url": "https://user:password@example.org"},
            {"title": "Nguồn 2", "url": "http://example.com/paper", "content": "A" * 1000},
        ]
        sources = normalize(results)
        self.assertEqual([item["title"] for item in sources], ["Đáng tin", "Nguồn 2"])
        self.assertEqual(len(sources[1]["content"]), 900)
        self.assertEqual(len(normalize(results, limit=1)), 1)


if __name__ == "__main__":
    unittest.main()
