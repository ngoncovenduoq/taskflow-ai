"""Offline tests for generic clone-and-run setup; never contacts an AI API."""

import io
import os
from pathlib import Path
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import app_launcher
import setup_local


class LocalSetupTests(unittest.TestCase):
    def test_new_clone_creates_local_config_without_echoing_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            env_file = Path(folder) / "backend" / ".env"
            output = io.StringIO()
            keys = iter(["sk-example", "tvly-example"])
            with patch("sys.stdout", output):
                result = setup_local.configure_api_keys(
                    env_file, ask_secret=lambda prompt: next(keys)
                )
            self.assertEqual(result, 0)
            content = env_file.read_text(encoding="utf-8")
            self.assertIn('OPENROUTER_API_KEY="sk-example"', content)
            self.assertIn('TAVILY_API_KEY="tvly-example"', content)
            self.assertNotIn("sk-example", output.getvalue())
            self.assertNotIn("tvly-example", output.getvalue())

    def test_existing_config_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            env_file = Path(folder) / "backend" / ".env"
            env_file.parent.mkdir(parents=True)
            env_file.write_text("OPENROUTER_API_KEY=existing", encoding="utf-8")
            self.assertEqual(setup_local.configure_api_keys(env_file), 0)
            self.assertEqual(env_file.read_text(encoding="utf-8"), "OPENROUTER_API_KEY=existing")

    def test_empty_key_does_not_create_config(self):
        with tempfile.TemporaryDirectory() as folder:
            env_file = Path(folder) / "backend" / ".env"
            self.assertEqual(setup_local.configure_api_keys(env_file, ask_secret=lambda prompt: ""), 1)
            self.assertFalse(env_file.exists())


class AppLauncherTests(unittest.TestCase):
    def test_validate_project_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            backend = root / "backend"
            with patch.object(app_launcher, "ROOT", root), patch.object(app_launcher, "BACKEND", backend):
                self.assertIn(str(Path("backend") / "main.py"), app_launcher.validate_project())
                for name in (
                    "main.py", "agent.py", "research_search.py", "writing_agent.py",
                    "usage_tracker.py", "api_errors.py", "frontend/index.html",
                ):
                    path = backend / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.touch()
                self.assertEqual(app_launcher.validate_project(), [])

    def test_browser_opens_after_successful_health(self):
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        with patch.object(app_launcher, "urlopen", return_value=response), \
             patch.object(app_launcher.json, "load", return_value={"status": "ok"}), \
             patch.object(app_launcher.webbrowser, "open") as open_browser:
            app_launcher.open_browser_when_ready(threading.Event())
        open_browser.assert_called_once_with(app_launcher.APP_URL)

    def test_missing_key_does_not_start_server(self):
        with patch.object(app_launcher, "validate_project", return_value=[]), \
             patch.object(app_launcher, "has_api_key", return_value=False), \
             patch.object(app_launcher.subprocess, "run") as run:
            self.assertEqual(app_launcher.main(), 1)
        run.assert_not_called()

    def test_existing_local_key_runs_normal_backend(self):
        with patch.object(app_launcher, "validate_project", return_value=[]), \
             patch.object(app_launcher, "has_api_key", return_value=True), \
             patch.object(app_launcher, "port_is_free", return_value=True), \
             patch.object(app_launcher.threading, "Thread"), \
             patch.object(app_launcher.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            self.assertEqual(app_launcher.main(), 0)
        self.assertEqual(run.call_args.args[0][1:4], ["-m", "uvicorn", "main:app"])
        self.assertEqual(run.call_args.kwargs["cwd"], app_launcher.BACKEND)
        self.assertNotIn("env", run.call_args.kwargs)

    def test_environment_key_is_accepted(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-realistic-example"}):
            self.assertTrue(app_launcher.has_api_key())


if __name__ == "__main__":
    unittest.main()
