"""Run with: python -m unittest test_api_errors.py -v

These tests only use synthetic errors; they do not call OpenRouter or Tavily.
"""

import unittest

from api_errors import to_http_exception


class FakeAPIError(Exception):
    def __init__(self, status_code: int):
        super().__init__("Synthetic API failure")
        self.status_code = status_code


class ErrorHandlingTests(unittest.TestCase):
    def test_openrouter_insufficient_credit(self):
        response = to_http_exception(FakeAPIError(402))
        self.assertEqual(response.status_code, 402)
        self.assertEqual(response.detail["code"], "AI_CREDITS_EXHAUSTED")

    def test_rate_limit(self):
        response = to_http_exception(FakeAPIError(429))
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.detail["code"], "RATE_LIMITED")

    def test_large_request(self):
        response = to_http_exception(FakeAPIError(413))
        self.assertEqual(response.status_code, 413)

    def test_timeout(self):
        response = to_http_exception(FakeAPIError(504))
        self.assertEqual(response.status_code, 504)

    def test_provider_unavailable(self):
        response = to_http_exception(FakeAPIError(503))
        self.assertEqual(response.status_code, 503)

    def test_unexpected_exception(self):
        response = to_http_exception(ValueError("No private details should leak"))
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private details", str(response.detail))


if __name__ == "__main__":
    unittest.main()
