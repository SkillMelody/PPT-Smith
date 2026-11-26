import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image

from engine.design_scene import html_import as hi
from engine.design_scene.cli import _html_surface
from engine.design_scene.runtime import ProcessFailed


class BrowserCapabilityTests(unittest.TestCase):
    def test_headless_shell_on_path_and_explicit_override(self):
        with TemporaryDirectory() as tmp:
            for name in ("chrome-headless-shell", "chromium"):
                path = Path(tmp, name)
                path.touch()
                path.chmod(0o755)
            with patch.dict(os.environ, {"PATH": tmp, "PPTSMITH_BROWSER": ""}):
                if os.name != "nt":
                    self.assertEqual(hi.find_browser(), str(Path(tmp, "chrome-headless-shell")))
                with patch.dict(os.environ, {"PPTSMITH_BROWSER": str(Path(tmp, "chromium"))}):
                    self.assertEqual(hi.find_browser(), str(Path(tmp, "chromium")))

    def test_mac_uses_mock_keychain_and_does_not_redirect_login_home(self):
        with TemporaryDirectory() as tmp, patch.object(sys, "platform", "darwin"):
            root = Path(tmp)
            with patch.dict(os.environ, {"HOME": "/Users/test-user"}):
                env = hi._browser_environment(root)
            self.assertEqual(env["HOME"], "/Users/test-user")
            self.assertIn("--use-mock-keychain", hi._browser_args("chrome", root, 320, 180))

    def test_installed_executable_that_cannot_render_is_unavailable(self):
        # A real executable with a deterministic rejection of Chromium's command-line options.
        with patch.dict(os.environ, {"PPTSMITH_BROWSER": sys.executable}):
            result = _html_surface()
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "HTML_BROWSER_LAUNCH_FAILED")
        self.assertEqual(result["fallback"]["command"], "author")
        self.assertIn("exit ", result["detail"])
        self.assertNotIn("missing", result)

    def test_distinguishes_missing_browser_and_permission_evidence(self):
        with patch.dict(os.environ, {"PPTSMITH_BROWSER": ""}), patch.object(hi, "find_browser", return_value=None):
            self.assertEqual(_html_surface()["reason"], "HTML_BROWSER_NOT_FOUND")
        with patch.dict(os.environ, {"PPTSMITH_BROWSER": "/nonexistent/pptsmith-browser"}):
            override = _html_surface()
            self.assertEqual(override["reason"], "HTML_BROWSER_OVERRIDE_INVALID")
            self.assertIn("next_action", override)
        error = ProcessFailed("chrome", 1, b"", b"Crashpad: Operation not permitted")
        with patch.object(hi, "find_browser", return_value="chrome"), patch.object(hi, "run_process", side_effect=error):
            blocked = _html_surface()
            self.assertEqual(blocked["reason"], "HTML_BROWSER_SANDBOX_BLOCKED")
            self.assertEqual(blocked["browser"], "chrome")
            self.assertEqual(blocked["cause"], "browser_permission_blocked")
        nested = ProcessFailed("chrome", -5, b"", b"sandbox initialization failed: Operation not permitted\nGPU process isn't usable.")
        with patch.object(hi, "find_browser", return_value="/opt/chrome-headless-shell"), \
                patch.object(hi, "run_process", side_effect=nested):
            nested_res = _html_surface()
            self.assertEqual(nested_res["reason"], "HTML_BROWSER_SANDBOX_BLOCKED")
            self.assertEqual(nested_res["browser"], "/opt/chrome-headless-shell")
            self.assertEqual(nested_res["cause"], "nested_browser_sandbox_blocked")
            self.assertIn("next_action", nested_res)

    def test_one_invocation_produces_both_outputs_using_private_directories(self):
        def headless(args, *, cwd, timeout, env):
            self.assertIn("--dump-dom", args)
            keys = ["XDG_CONFIG_HOME", "XDG_CACHE_HOME", "TMPDIR"]
            if sys.platform != "darwin":
                keys.append("HOME")
            for key in keys:
                self.assertEqual(Path(env[key]).parent, cwd)
                self.assertTrue(Path(env[key]).is_dir())
            shot = next(arg.split("=", 1)[1] for arg in args if arg.startswith("--screenshot="))
            Image.new("RGB", (320, 180)).save(shot)
            return ('<pre id="__pptsmith_layout">{"width":320,"height":180,"items":'
                    '[{"kind":"text","runs":[{"text":"pptsmith-probe"}]}]}</pre>')
        with patch.object(hi, "find_browser", return_value="chrome"), patch.object(hi, "run_process", side_effect=headless) as run:
            self.assertTrue(_html_surface()["available"])
        self.assertEqual(run.call_count, 1)

    def test_mac_sandbox_parameter_failure_reports_host_recovery_without_home_retry(self):
        stderr = (b"[1125/165930.106964:ERROR:net/dns/dns_config_service_posix.cc:138] DNS config watch failed to start.\n"
                  b"[1125/165930.110195:FATAL:content/browser/sandbox_parameters_mac.mm:67] "
                  b"Check failed: . : Input/output error (5)\n" + b"Chromium shutdown output\n" * 80)
        error = ProcessFailed("chrome-headless-shell", -5, b"", stderr)
        with patch.object(sys, "platform", "darwin"), \
                patch.object(hi, "find_browser", return_value="chrome-headless-shell"), \
                patch.object(hi, "run_process", side_effect=error) as run:
            result = _html_surface()
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "HTML_BROWSER_SANDBOX_BLOCKED")
        self.assertEqual(result["cause"], "nested_browser_sandbox_blocked")
        self.assertIn("approved execution path", result["next_action"])
        self.assertIn("sandbox_parameters_mac.mm:67", result["detail"])
        self.assertEqual(run.call_count, 1)

    def test_shutdown_watchdog_still_requires_both_outputs(self):
        dom = (b'<pre id="__pptsmith_layout">{"width":320,"height":180,"items":'
               b'[{"kind":"text","runs":[{"text":"pptsmith-probe"}]}]}</pre>')
        watchdog = b"Teardown watchdog expired; recording dump and terminating."
        cases = [(2, dom, watchdog, True, None),
                 (2, dom, b"Other exit error", True, "HTML_BROWSER_LAUNCH_FAILED"),
                 (2, b"", watchdog, True, "HTML_LAYOUT_EXTRACTION_FAILED"),
                 (2, dom, watchdog, False, "HTML_BROWSER_PREVIEW_FAILED")]
        for code, stdout, stderr, write_png, reason in cases:
            with self.subTest(reason=reason):
                def browser(args, *, cwd, timeout, env):
                    if write_png:
                        Image.new("RGB", (320, 180)).save(cwd / "preview.png")
                    raise ProcessFailed("chrome", code, stdout, stderr)
                with patch.object(hi, "find_browser", return_value="chrome"), patch.object(hi, "run_process", side_effect=browser):
                    result = _html_surface()
                self.assertEqual(result["available"], reason is None)
                self.assertEqual(result.get("reason"), reason)
                if result["available"]:
                    self.assertEqual(result["warning"]["exit_code"], 2)

    def test_missing_screenshot_prevents_positive_probe(self):
        with patch.object(hi, "find_browser", return_value="chrome"), patch.object(hi, "run_process", return_value=""):
            self.assertEqual(_html_surface()["reason"], "HTML_BROWSER_PREVIEW_FAILED")

    def test_mac_sandbox_retry_succeeds_with_isolated_home(self):
        seen_homes = []

        def retry_browser(args, *, cwd, timeout, env):
            seen_homes.append(env.get("HOME"))
            if len(seen_homes) == 1:
                raise ProcessFailed("chrome", -5, b"", b"Crashpad: Operation not permitted")
            shot = next(arg.split("=", 1)[1] for arg in args if arg.startswith("--screenshot="))
            Image.new("RGB", (320, 180)).save(shot)
            return ('<pre id="__pptsmith_layout">{"width":320,"height":180,"items":'
                    '[{"kind":"text","runs":[{"text":"pptsmith-probe"}]}]}</pre>')

        with patch.object(sys, "platform", "darwin"), \
                patch.dict(os.environ, {"HOME": "/Users/test-user"}), \
                patch.object(hi, "find_browser", return_value="chrome"), \
                patch.object(hi, "run_process", side_effect=retry_browser):
            result = _html_surface()
        self.assertTrue(result["available"])
        self.assertEqual(seen_homes[0], "/Users/test-user")
        self.assertNotEqual(seen_homes[1], "/Users/test-user")
