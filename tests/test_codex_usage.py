import json
import os
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "bin" / "codex-usage"
FAKE_CODEX = Path(__file__).resolve().parent / "fake_codex.py"


def load_script():
    # The command has no .py suffix, so the usual import machinery does not find it.
    loader = SourceFileLoader("codex_usage", str(SCRIPT))
    module = module_from_spec(spec_from_loader("codex_usage", loader))
    loader.exec_module(module)
    return module


codex_usage = load_script()


def window(used, minutes, resets_at=1796097689):
    return {"usedPercent": used, "windowDurationMins": minutes, "resetsAt": resets_at}


class SummarizeTest(unittest.TestCase):
    def test_weekly_window_only(self):
        result = {
            "rateLimits": {"primary": window(30, 10080), "secondary": None},
            "rateLimitResetCredits": {"availableCount": 2},
        }
        self.assertEqual(codex_usage.summarize(result), {
            "remainingPercent": 70,
            "windowMinutes": 10080,
            "resetsAt": 1796097689,
            "freeResets": 2,
        })

    def test_the_more_used_window_wins(self):
        result = {"rateLimits": {"primary": window(30, 10080), "secondary": window(80.5, 300, 42)}}
        summary = codex_usage.summarize(result)
        self.assertEqual(summary["remainingPercent"], 19)
        self.assertEqual(summary["windowMinutes"], 300)
        self.assertEqual(summary["resetsAt"], 42)
        self.assertEqual(summary["freeResets"], 0)

    def test_overused_window_is_clamped_to_zero(self):
        result = {"rateLimits": {"primary": window(104, 10080)}}
        self.assertEqual(codex_usage.summarize(result)["remainingPercent"], 0)

    def test_no_windows_is_an_error(self):
        with self.assertRaises(codex_usage.UsageError) as caught:
            codex_usage.summarize({"rateLimits": {"primary": None, "secondary": None}})
        self.assertEqual(caught.exception.code, "no_limits")


class AppServerTest(unittest.TestCase):
    def read(self, mode, timeout=5):
        os.environ["FAKE_CODEX_MODE"] = mode
        try:
            return codex_usage.read_rate_limits(codex=str(FAKE_CODEX), timeout=timeout)
        finally:
            del os.environ["FAKE_CODEX_MODE"]

    def assert_fails(self, code, mode, **kwargs):
        with self.assertRaises(codex_usage.UsageError) as caught:
            self.read(mode, **kwargs)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_reads_rate_limits(self):
        result = self.read("ok")
        self.assertEqual(result["rateLimits"]["primary"]["usedPercent"], 30)

    def test_missing_login_is_explained(self):
        self.assert_fails("not_logged_in", "auth_error")

    def test_other_server_errors_keep_their_text(self):
        error = self.assert_fails("codex_error", "rpc_error")
        self.assertEqual(error.detail, "something broke")

    def test_hung_app_server_times_out(self):
        self.assert_fails("timeout", "hang", timeout=1)

    def test_app_server_exiting_early(self):
        self.assert_fails("no_answer", "exit")

    def test_missing_codex(self):
        with self.assertRaises(codex_usage.UsageError) as caught:
            codex_usage.read_rate_limits(codex="/nonexistent/codex")
        self.assertEqual(caught.exception.code, "codex_not_found")


class CommandLineTest(unittest.TestCase):
    def run_cli(self, mode):
        with tempfile.TemporaryDirectory() as bindir:
            os.symlink(FAKE_CODEX, Path(bindir) / "codex")
            env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}", FAKE_CODEX_MODE=mode)
            done = subprocess.run([str(SCRIPT)], env=env, capture_output=True, text=True, timeout=30)
        return done.returncode, json.loads(done.stdout)

    def test_prints_summary(self):
        status, output = self.run_cli("ok")
        self.assertEqual(status, 0)
        self.assertEqual(output["remainingPercent"], 70)

    def test_prints_error(self):
        status, output = self.run_cli("auth_error")
        self.assertEqual(status, 1)
        self.assertEqual(output, {"error": "not_logged_in"})


if __name__ == "__main__":
    unittest.main()
