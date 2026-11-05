"""Smoke tests for durable SQLite conversations; do not modify the user's database."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import chat_history


class ChatHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(chat_history, "DB_PATH", Path(self.temp.name) / "history.db")
        self.db_patch.start()
        chat_history.init_chat_db()

    def tearDown(self):
        self.db_patch.stop()
        self.temp.cleanup()

    def test_create_store_reopen_and_delete(self):
        record = chat_history.create_conversation()
        cid = record["id"]
        self.assertEqual(chat_history.get_conversations()[0]["message_count"], 0)

        user = chat_history.add_conversation_message(cid, "user", "Hãy lập kế hoạch hôm nay")
        answer = chat_history.add_conversation_message(cid, "assistant", "**Kế hoạch**: Ôn NLP")
        self.assertGreater(answer["id"], user["id"])
        self.assertEqual(chat_history.get_conversations()[0]["title"], "Hãy lập kế hoạch hôm nay")
        self.assertEqual(chat_history.get_conversations()[0]["message_count"], 2)
        self.assertEqual([m["role"] for m in chat_history.get_conversation_messages(cid)], ["user", "assistant"])

        self.assertTrue(chat_history.delete_conversation(cid))
        self.assertIsNone(chat_history.get_conversation_messages(cid))
        self.assertFalse(chat_history.delete_conversation(cid))
        self.assertEqual(chat_history.get_conversations(), [])

    def test_missing_conversation_does_not_create_orphan_messages(self):
        self.assertIsNone(chat_history.add_conversation_message(99999, "user", "Xin chào"))
        self.assertIsNone(chat_history.get_conversation_messages(99999))

    def test_messages_are_limited_to_newest_200_in_correct_order(self):
        cid = chat_history.create_conversation()["id"]
        for count in range(205):
            chat_history.add_conversation_message(cid, "user", f"Tin nhắn {count}")
        messages = chat_history.get_conversation_messages(cid)
        self.assertEqual(len(messages), 200)
        self.assertEqual(messages[0]["content"], "Tin nhắn 5")
        self.assertEqual(messages[-1]["content"], "Tin nhắn 204")

    def test_model_context_skips_current_prompt_and_unanswered_prompts(self):
        cid = chat_history.create_conversation()["id"]
        chat_history.add_conversation_message(cid, "user", "Tạo công việc học NLP")
        chat_history.add_conversation_message(cid, "assistant", "Đã tạo công việc #3")
        chat_history.add_conversation_message(cid, "user", "Xóa công việc #3")  # Failed call
        chat_history.add_conversation_message(cid, "user", "Công việc đó có deadline không?")

        context = chat_history.get_recent_conversation_context(
            cid, "Công việc đó có deadline không?"
        )
        self.assertEqual(context, [
            {"role": "user", "content": "Tạo công việc học NLP"},
            {"role": "assistant", "content": "Đã tạo công việc #3"},
        ])

    def test_model_context_uses_latest_complete_turns_with_budget(self):
        cid = chat_history.create_conversation()["id"]
        for n in range(7):
            chat_history.add_conversation_message(cid, "user", f"Yêu cầu {n}")
            chat_history.add_conversation_message(cid, "assistant", f"Trả lời {n}")
        context = chat_history.get_recent_conversation_context(cid, "Tin nhắn mới")
        self.assertEqual(len(context), 8)
        self.assertEqual(context[0]["content"], "Yêu cầu 3")
        self.assertEqual(context[-1]["content"], "Trả lời 6")
        shorter = chat_history.get_recent_conversation_context(
            cid, "Tin nhắn mới", max_turns=4, max_chars=30
        )
        self.assertEqual(shorter, [
            {"role": "user", "content": "Yêu cầu 6"},
            {"role": "assistant", "content": "Trả lời 6"},
        ])

    def test_model_context_never_loads_other_conversation(self):
        first = chat_history.create_conversation()["id"]
        second = chat_history.create_conversation()["id"]
        chat_history.add_conversation_message(first, "user", "Thông tin riêng")
        chat_history.add_conversation_message(first, "assistant", "Đã hiểu")
        self.assertEqual(chat_history.get_recent_conversation_context(second, "Chào"), [])
        self.assertIsNone(chat_history.get_recent_conversation_context(999, "Chào"))

    def test_recall_questions_are_recognized_without_blocking_pdf_queries(self):
        self.assertTrue(chat_history.asks_about_prior_chat("Lúc nãy tôi đang học chủ đề gì?"))
        self.assertTrue(chat_history.asks_about_prior_chat("Trước đó chúng ta đã nói về vấn đề gì?"))
        self.assertTrue(chat_history.asks_about_prior_chat("What did we discuss earlier?"))
        self.assertFalse(chat_history.asks_about_prior_chat("Hãy tóm tắt Report.pdf cho tôi."))
        self.assertFalse(chat_history.asks_about_prior_chat("Lúc nãy tôi tải PDF, hãy tóm tắt chương 1."))
        self.assertFalse(chat_history.asks_about_prior_chat("Tìm trong PDF chủ đề Transformer."))


if __name__ == "__main__":
    unittest.main()
