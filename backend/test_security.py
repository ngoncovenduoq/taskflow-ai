"""Offline security checks; no OpenRouter key or FastAPI server required."""

import unittest

from security import is_allowed_browser_request as allowed


class LocalBrowserSecurityTests(unittest.TestCase):
    def test_local_ui_and_same_origin_writes(self):
        self.assertTrue(allowed("GET", "http", "127.0.0.1:8000"))
        self.assertTrue(allowed("GET", "http", "localhost:8000"))
        self.assertTrue(allowed("POST", "http", "127.0.0.1:8000", "http://127.0.0.1:8000", "same-origin"))
        self.assertTrue(allowed("POST", "http", "localhost:8000", None, None))
        self.assertTrue(allowed("POST", "http", "[::1]:8000", "http://[::1]:8000", "same-origin"))

    def test_rejects_foreign_hosts_and_dns_rebinding(self):
        for host in ("evil.example", "evil.example:8000", "127.0.0.1.evil.example", "127.0.0.1@evil.example", "localhost:bad"):
            with self.subTest(host=host):
                self.assertFalse(allowed("GET", "http", host))

    def test_rejects_cross_origin_mutations(self):
        for origin in ("https://evil.example", "null", "http://localhost:8000", "http://127.0.0.1:9999", "http://127.0.0.1:8000.evil.example"):
            with self.subTest(origin=origin):
                self.assertFalse(allowed("POST", "http", "127.0.0.1:8000", origin))
        self.assertFalse(allowed("DELETE", "http", "127.0.0.1:8000", None, "cross-site"))
        self.assertFalse(allowed("POST", "http", "127.0.0.1:8000", None, "same-site"))


if __name__ == "__main__":
    unittest.main()
