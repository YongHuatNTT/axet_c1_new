import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logscope.cli import main

SAMPLE_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "sample.log")


def _write_temp_log(content: str) -> str:
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8")
    handle.write(content)
    handle.close()
    return handle.name


def _run_cli(argv):
    """Run ``main(argv)`` capturing stdout/stderr. Returns (exit_code, stdout, stderr)."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = main(argv)
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 2
    return exit_code, stdout.getvalue(), stderr.getvalue()


SAMPLE_CONTENT = (
    "2026-10-01 09:00:00 INFO Application started\n"
    "2026-10-01 09:01:00 WARN Slow response detected\n"
    "2026-10-01 09:02:00 ERROR Database connection failed\n"
    "malformed line without timestamp and level\n"
    "2026-10-01 09:15:00 ERROR Timeout while calling payment API\n"
)


class CliExitCodeTests(unittest.TestCase):
    def test_missing_file_returns_exit_code_1(self):
        exit_code, _stdout, stderr = _run_cli(["summary", "does_not_exist.log"])
        self.assertEqual(exit_code, 1)
        self.assertIn("log file not found", stderr)

    def test_missing_file_timeline_returns_exit_code_1(self):
        exit_code, _stdout, stderr = _run_cli(["timeline", "does_not_exist.log"])
        self.assertEqual(exit_code, 1)
        self.assertIn("log file not found", stderr)

    def test_missing_file_grep_returns_exit_code_1(self):
        exit_code, _stdout, stderr = _run_cli(["grep", "does_not_exist.log"])
        self.assertEqual(exit_code, 1)
        self.assertIn("log file not found", stderr)

    def test_invalid_bucket_returns_exit_code_2(self):
        path = _write_temp_log(SAMPLE_CONTENT)
        try:
            exit_code, _stdout, stderr = _run_cli(["timeline", path, "--bucket", "15x"])
        finally:
            os.remove(path)
        self.assertEqual(exit_code, 2)
        self.assertIn("invalid bucket interval", stderr)

    def test_invalid_since_returns_exit_code_2(self):
        path = _write_temp_log(SAMPLE_CONTENT)
        try:
            exit_code, _stdout, stderr = _run_cli(["grep", path, "--since", "garbage"])
        finally:
            os.remove(path)
        self.assertEqual(exit_code, 2)
        self.assertIn("invalid --since value", stderr)

    def test_invalid_level_choice_returns_exit_code_2(self):
        path = _write_temp_log(SAMPLE_CONTENT)
        try:
            exit_code, _stdout, stderr = _run_cli(["grep", path, "--level", "DEBUG"])
        finally:
            os.remove(path)
        self.assertEqual(exit_code, 2)
        self.assertIn("invalid choice", stderr)

    def test_successful_summary_returns_exit_code_0(self):
        path = _write_temp_log(SAMPLE_CONTENT)
        try:
            exit_code, stdout, _stderr = _run_cli(["summary", path])
        finally:
            os.remove(path)
        self.assertEqual(exit_code, 0)
        self.assertIn("logscope summary", stdout)


class CliTextOutputTests(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_log(SAMPLE_CONTENT)

    def tearDown(self):
        os.remove(self.path)

    def test_summary_text_output(self):
        exit_code, stdout, _stderr = _run_cli(["summary", self.path])
        self.assertEqual(exit_code, 0)
        self.assertIn("ERROR count: 2", stdout)
        self.assertIn("Malformed lines: 1", stdout)

    def test_timeline_text_output(self):
        exit_code, stdout, _stderr = _run_cli(["timeline", self.path, "--bucket", "15m"])
        self.assertEqual(exit_code, 0)
        self.assertIn("2026-10-01 09:00", stdout)
        self.assertIn("Malformed lines: 1", stdout)

    def test_grep_text_output(self):
        exit_code, stdout, _stderr = _run_cli(["grep", self.path, "--level", "ERROR"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Database connection failed", stdout)
        self.assertIn("Malformed lines skipped: 1", stdout)


class CliJsonOutputTests(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_log(SAMPLE_CONTENT)

    def tearDown(self):
        os.remove(self.path)

    def test_summary_json_output(self):
        exit_code, stdout, _stderr = _run_cli(["summary", self.path, "--format", "json"])
        self.assertEqual(exit_code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["error_count"], 2)
        self.assertEqual(data["malformed_count"], 1)

    def test_timeline_json_output(self):
        exit_code, stdout, _stderr = _run_cli(
            ["timeline", self.path, "--bucket", "15m", "--format", "json"]
        )
        self.assertEqual(exit_code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["malformed_count"], 1)
        self.assertEqual(len(data["buckets"]), 2)

    def test_grep_json_output(self):
        exit_code, stdout, _stderr = _run_cli(
            ["grep", self.path, "--level", "ERROR", "--format", "json"]
        )
        self.assertEqual(exit_code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["match_count"], 2)
        self.assertEqual(data["malformed_count"], 1)


class CliMarkdownOutputTests(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_log(SAMPLE_CONTENT)
        self._written_reports = []

    def tearDown(self):
        os.remove(self.path)
        for report_path in self._written_reports:
            Path(report_path).unlink(missing_ok=True)

    def _extract_report_path(self, stdout: str) -> str:
        prefix = "Markdown report written to: "
        line = next(line for line in stdout.splitlines() if line.startswith(prefix))
        return line[len(prefix):].strip()

    def test_summary_md_output_writes_report_file(self):
        exit_code, stdout, _stderr = _run_cli(["summary", self.path, "--format", "md"])
        self.assertEqual(exit_code, 0)
        report_path = self._extract_report_path(stdout)
        self._written_reports.append(report_path)
        self.assertTrue(Path(report_path).exists())
        content = Path(report_path).read_text(encoding="utf-8")
        self.assertIn("logscope summary report", content)

    def test_timeline_md_output_writes_report_file(self):
        exit_code, stdout, _stderr = _run_cli(
            ["timeline", self.path, "--bucket", "15m", "--format", "md"]
        )
        self.assertEqual(exit_code, 0)
        report_path = self._extract_report_path(stdout)
        self._written_reports.append(report_path)
        self.assertTrue(Path(report_path).exists())

    def test_grep_md_output_writes_report_file(self):
        exit_code, stdout, _stderr = _run_cli(["grep", self.path, "--format", "md"])
        self.assertEqual(exit_code, 0)
        report_path = self._extract_report_path(stdout)
        self._written_reports.append(report_path)
        self.assertTrue(Path(report_path).exists())


class CliSampleLogIntegrationTests(unittest.TestCase):
    """End-to-end smoke tests against the real, committed sample.log."""

    def setUp(self):
        self.assertTrue(
            os.path.exists(SAMPLE_LOG_PATH), f"sample.log not found at {SAMPLE_LOG_PATH}"
        )

    def test_summary_on_sample_log(self):
        exit_code, stdout, _stderr = _run_cli(["summary", SAMPLE_LOG_PATH])
        self.assertEqual(exit_code, 0)
        self.assertIn("INFO count:  5", stdout)
        self.assertIn("WARN count:  3", stdout)
        self.assertIn("ERROR count: 6", stdout)
        self.assertIn("Malformed lines: 2", stdout)
        self.assertIn("Database connection failed", stdout)
        self.assertIn("First timestamp: 2026-10-01 09:00:00", stdout)
        self.assertIn("Last timestamp:  2026-10-01 09:22:00", stdout)

    def test_summary_json_on_sample_log(self):
        exit_code, stdout, _stderr = _run_cli(["summary", SAMPLE_LOG_PATH, "--format", "json"])
        self.assertEqual(exit_code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["info_count"], 5)
        self.assertEqual(data["warn_count"], 3)
        self.assertEqual(data["error_count"], 6)
        self.assertEqual(data["malformed_count"], 2)
        self.assertEqual(data["top_errors"][0]["message"], "Database connection failed")
        self.assertEqual(data["top_errors"][0]["count"], 3)

    def test_timeline_on_sample_log(self):
        exit_code, stdout, _stderr = _run_cli(["timeline", SAMPLE_LOG_PATH, "--bucket", "15m"])
        self.assertEqual(exit_code, 0)
        self.assertIn("2026-10-01 09:00", stdout)
        self.assertIn("2026-10-01 09:15", stdout)
        self.assertIn("Malformed lines: 2", stdout)

    def test_timeline_json_on_sample_log(self):
        exit_code, stdout, _stderr = _run_cli(
            ["timeline", SAMPLE_LOG_PATH, "--bucket", "15m", "--format", "json"]
        )
        self.assertEqual(exit_code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["malformed_count"], 2)
        buckets = {b["start"]: b["error_count"] for b in data["buckets"]}
        self.assertEqual(buckets["2026-10-01 09:00:00"], 3)
        self.assertEqual(buckets["2026-10-01 09:15:00"], 3)

    def test_grep_level_filter_on_sample_log(self):
        exit_code, stdout, _stderr = _run_cli(["grep", SAMPLE_LOG_PATH, "--level", "ERROR"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Malformed lines skipped: 2", stdout)
        matched_lines = [
            line for line in stdout.splitlines() if line.startswith("2026-10-01")
        ]
        self.assertEqual(len(matched_lines), 6)
        self.assertTrue(all(" ERROR " in line for line in matched_lines))

    def test_grep_since_filter_on_sample_log(self):
        exit_code, stdout, _stderr = _run_cli(
            ["grep", SAMPLE_LOG_PATH, "--level", "ERROR", "--since", "2026-10-01 09:00"]
        )
        self.assertEqual(exit_code, 0)
        matched_lines = [
            line for line in stdout.splitlines() if line.startswith("2026-10-01")
        ]
        self.assertEqual(len(matched_lines), 6)

    def test_grep_json_on_sample_log(self):
        exit_code, stdout, _stderr = _run_cli(
            ["grep", SAMPLE_LOG_PATH, "--level", "ERROR", "--format", "json"]
        )
        self.assertEqual(exit_code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["match_count"], 6)
        self.assertEqual(data["malformed_count"], 2)


if __name__ == "__main__":
    unittest.main()
