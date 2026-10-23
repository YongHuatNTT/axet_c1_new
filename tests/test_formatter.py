import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logscope.formatter import generate_report_filename, render_json, write_markdown_report
from logscope.grep import compute_grep, render_grep_markdown_lines
from logscope.summary import compute_summary, render_summary_markdown_lines
from logscope.timeline import compute_timeline, render_timeline_markdown_lines


def _write_temp_log(content: str) -> str:
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8")
    handle.write(content)
    handle.close()
    return handle.name


SAMPLE_CONTENT = (
    "2026-10-01 09:00:00 INFO Application started\n"
    "2026-10-01 09:02:00 ERROR Database connection failed\n"
    "malformed line without timestamp and level\n"
    "2026-10-01 09:15:00 ERROR Timeout while calling payment API\n"
)


class RenderJsonTests(unittest.TestCase):
    def test_render_json_roundtrips(self):
        data = {"a": 1, "b": [1, 2, 3]}
        text = render_json(data)
        self.assertEqual(json.loads(text), data)


class ReportFilenameTests(unittest.TestCase):
    def test_filename_contains_command_and_extension(self):
        name = generate_report_filename("summary")
        self.assertTrue(name.startswith("logscope_summary_"))
        self.assertTrue(name.endswith(".md"))


class MarkdownReportWritingTests(unittest.TestCase):
    def test_write_markdown_report_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = write_markdown_report("summary", "Test Report", ["- line one", "- line two"])
            try:
                self.assertTrue(path.exists())
                content = path.read_text(encoding="utf-8")
                self.assertIn("# Test Report", content)
                self.assertIn("line one", content)
            finally:
                path.unlink(missing_ok=True)


class CommandJsonOutputTests(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_log(SAMPLE_CONTENT)

    def tearDown(self):
        os.remove(self.path)

    def test_summary_to_dict_is_json_serializable(self):
        result = compute_summary(self.path)
        text = render_json(result.to_dict())
        data = json.loads(text)
        self.assertEqual(data["malformed_count"], 1)
        self.assertEqual(data["error_count"], 2)

    def test_timeline_to_dict_is_json_serializable(self):
        result = compute_timeline(self.path, "15m")
        text = render_json(result.to_dict())
        data = json.loads(text)
        self.assertEqual(data["malformed_count"], 1)
        self.assertEqual(len(data["buckets"]), 2)

    def test_grep_to_dict_is_json_serializable(self):
        result = compute_grep(self.path, level="ERROR")
        text = render_json(result.to_dict())
        data = json.loads(text)
        self.assertEqual(data["match_count"], 2)
        self.assertEqual(data["malformed_count"], 1)


class CommandMarkdownLinesTests(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_log(SAMPLE_CONTENT)

    def tearDown(self):
        os.remove(self.path)

    def test_summary_markdown_lines_contains_counts(self):
        result = compute_summary(self.path)
        lines = render_summary_markdown_lines(result)
        joined = "\n".join(lines)
        self.assertIn("| ERROR | 2 |", joined)
        self.assertIn("Malformed line count: 1", joined)

    def test_timeline_markdown_lines_contains_bucket_table(self):
        result = compute_timeline(self.path, "15m")
        lines = render_timeline_markdown_lines(result)
        joined = "\n".join(lines)
        self.assertIn("Bucket start", joined)
        self.assertIn("Malformed line count: 1", joined)

    def test_grep_markdown_lines_contains_match_table(self):
        result = compute_grep(self.path, level="ERROR")
        lines = render_grep_markdown_lines(result)
        joined = "\n".join(lines)
        self.assertIn("Match count: 2", joined)
        self.assertIn("Database connection failed", joined)


if __name__ == "__main__":
    unittest.main()
