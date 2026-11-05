"""PDF indexing and scoped search regression tests, using temporary files.

The fake collection follows the subset of Chroma's API used by rag_store.
No actual Chroma installation, embedding download, or real PDF is required.
"""

import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FakeCollection:
    def __init__(self):
        self.rows = {}

    def count(self):
        return len(self.rows)

    def get(self, where=None, include=None):
        rows = [
            (key, item) for key, item in self.rows.items()
            if where is None or all(item["metadata"].get(k) == v for k, v in where.items())
        ]
        return {
            "ids": [key for key, _ in rows],
            "metadatas": [item["metadata"] for _, item in rows],
            "documents": [item["text"] for _, item in rows],
        }

    def upsert(self, ids, documents, metadatas):
        for key, text, metadata in zip(ids, documents, metadatas):
            self.rows[key] = {"text": text, "metadata": metadata}

    def delete(self, ids):
        for key in ids:
            self.rows.pop(key, None)

    def query(self, query_texts, n_results, include, where=None):
        found = self.get(where)
        return {
            "documents": [found["documents"][:n_results]],
            "metadatas": [found["metadatas"][:n_results]],
        }


class RagStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.collection = FakeCollection()
        stub = types.ModuleType("chromadb")
        stub.PersistentClient = lambda path: types.SimpleNamespace(
            get_or_create_collection=lambda name: self.collection
        )
        file = Path(__file__).with_name("rag_store.py")
        spec = importlib.util.spec_from_file_location("taskflow_rag_store_under_test", file)
        self.rag = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"chromadb": stub}):
            spec.loader.exec_module(self.rag)
        self.rag.DOCUMENTS_DIR = Path(self.temp.name)

    def save_doc(self, document_id, filename, texts):
        path = self.rag.DOCUMENTS_DIR / f"{document_id}.json"
        path.write_text(json.dumps({
            "document_id": document_id,
            "filename": filename,
            "pages": [{"page": number, "text": text} for number, text in enumerate(texts, 1)],
        }), encoding="utf-8")

    def test_index_search_only_selected_pdf_and_delete(self):
        first, second = "a" * 32, "b" * 32
        self.save_doc(first, "Report.pdf", ["Bài toán quản lý tồn kho", "Giải pháp học sâu"])
        self.save_doc(second, "Other.pdf", ["Thông tin không liên quan"])
        self.assertEqual(self.rag.index_document(first), 2)
        self.assertEqual(self.rag.index_document(second), 1)
        self.assertEqual(len(self.rag.list_documents()), 2)
        result = self.rag.search_documents("Tóm tắt nội dung", document_id=first)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(item["filename"] == "Report.pdf" for item in result))
        self.assertEqual({item["page"] for item in result}, {1, 2})
        self.assertTrue(self.rag.delete_document(first))
        self.assertEqual(len(self.rag.list_documents()), 1)
        self.assertEqual(self.collection.count(), 1, "Deletion must preserve other PDFs")
        self.assertFalse(self.rag.delete_document(first))

    def test_reindex_removes_stale_chunks_and_prevents_path_traversal(self):
        document_id = "c" * 32
        self.save_doc(document_id, "Study.pdf", ["A" * 2000])
        self.assertEqual(self.rag.index_document(document_id), 3)
        self.save_doc(document_id, "Study.pdf", ["B" * 100])
        self.assertEqual(self.rag.index_document(document_id), 1)
        self.assertEqual(self.collection.count(), 1)
        self.assertTrue(self.rag.list_documents()[0]["indexed"])
        with self.assertRaises(ValueError):
            self.rag.delete_document("../tasks.db")

    def test_scoping_uses_ids_even_when_pdf_filenames_match(self):
        first, second = "d" * 32, "e" * 32
        self.save_doc(first, "Report.pdf", ["Chỉ có thông tin dự án A"])
        self.save_doc(second, "Report.pdf", ["Chỉ có thông tin dự án B"])
        self.rag.index_document(first)
        self.rag.index_document(second)
        first_result = self.rag.search_documents("dự án", document_id=first)
        second_result = self.rag.search_documents("dự án", document_id=second)
        self.assertEqual([item["text"] for item in first_result], ["Chỉ có thông tin dự án A"])
        self.assertEqual([item["text"] for item in second_result], ["Chỉ có thông tin dự án B"])

    def test_hybrid_search_recovers_relevant_later_pages_in_comparison(self):
        report_id, other_id = "f" * 32, "a" * 32
        pages = ["Trang giới thiệu và thông tin trường đại học"] * 12
        pages += ["Dự án tối ưu quản lý tồn kho sử dụng học sâu và học tăng cường"]
        pages += ["Thông tin chung của khoa"] * 2
        pages += ["Phương pháp dự báo tồn kho bằng Deep Learning và DDPG"]
        self.save_doc(report_id, "Report.pdf", pages)
        self.save_doc(other_id, "Other.pdf", ["Deep Learning và tồn kho của tài liệu khác"])
        self.rag.index_document(report_id)
        self.rag.index_document(other_id)
        result = self.rag.search_document_hybrid(
            "Hãy so sánh dự án tối ưu tồn kho trong CV.pdf và Report.pdf, "
            "nêu mục tiêu, phương pháp và kết quả", report_id, top_k=3,
        )
        self.assertTrue({13, 16}.issubset({item["page"] for item in result}))
        self.assertEqual(len(result), 3)
        self.assertTrue(all(item["filename"] == "Report.pdf" for item in result))


if __name__ == "__main__":
    unittest.main()
