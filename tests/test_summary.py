import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logscope.summary import compute_summary, render_summary_text


def _write_temp_log(content: str) -> str:
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8")
    handle.write(content)
    handle.close()
    return handle.name


SAMPLE_CONTENT = (
    "2026-10-01 09:00:00 INFO Application started\n"
    "2026-10-01 09:01:00 WARN Slow response detected\n"
    "2026-10-01 09:02:00 ERROR Database connection failed\n"
    "2026-10-01 09:03:00 INFO User login successful\n"
    "2026-10-01 09:04:00 ERROR Database connection failed\n"
    "malformed line without timestamp and level\n"
    "2026-10-01 09:06:00 ERROR Timeout while calling payment API\n"
    "2026-10-01 BADTS ERROR broken timestamp example\n"
    "2026-10-01 09:22:00 ERROR Disk space critically low\n"
)


class SummaryComputationTests(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_log(SAMPLE_CONTENT)

    def tearDown(self):
        os.remove(self.path)

    def test_level_counts(self):
        result = compute_summary(self.path)
        self.assertEqual(result.info_count, 2)
        self.assertEqual(result.warn_count, 1)
        self.assertEqual(result.error_count, 4)

    def test_malformed_count(self):
        result = compute_summary(self.path)
        self.assertEqual(result.malformed_count, 2)

    def test_first_and_last_timestamp(self):
        result = compute_summary(self.path)
        self.assertEqual(result.first_timestamp, datetime(2026, 10, 1, 9, 0, 0))
        self.assertEqual(result.last_timestamp, datetime(2026, 10, 1, 9, 22, 0))

    def test_top_errors_ordering(self):
        result = compute_summary(self.path)
        top_messages = [message for message, _count in result.top_errors]
        self.assertEqual(top_messages[0], "Database connection failed")
        self.assertEqual(result.top_errors[0][1], 2)
        self.assertLessEqual(len(result.top_errors), 5)

    def test_to_dict_contains_expected_keys(self):
        result = compute_summary(self.path)
        data = result.to_dict()
        self.assertIn("info_count", data)
        self.assertIn("top_errors", data)
        self.assertIn("malformed_count", data)
        self.assertEqual(data["first_timestamp"], "2026-10-01 09:00:00")


class SummaryEmptyAndMalformedOnlyTests(unittest.TestCase):
    def test_all_malformed_log(self):
        path = _write_temp_log("garbage line one\ngarbage line two\n")
        try:
            result = compute_summary(path)
        finally:
            os.remove(path)

        self.assertEqual(result.malformed_count, 2)
        self.assertEqual(result.info_count, 0)
        self.assertEqual(result.warn_count, 0)
        self.assertEqual(result.error_count, 0)
        self.assertIsNone(result.first_timestamp)
        self.assertIsNone(result.last_timestamp)
        self.assertEqual(result.top_errors, [])

    def test_empty_file(self):
        path = _write_temp_log("")
        try:
            result = compute_summary(path)
        finally:
            os.remove(path)

        self.assertEqual(result.malformed_count, 0)
        self.assertIsNone(result.first_timestamp)


class SummaryTextRenderingTests(unittest.TestCase):
    def test_render_contains_core_fields(self):
        path = _write_temp_log(SAMPLE_CONTENT)
        try:
            result = compute_summary(path)
        finally:
            os.remove(path)

        text = render_summary_text(result)
        self.assertIn("INFO count:  2", text)
        self.assertIn("WARN count:  1", text)
        self.assertIn("ERROR count: 4", text)
        self.assertIn("Malformed lines: 2", text)
        self.assertIn("Database connection failed", text)

    def test_render_handles_no_valid_records(self):
        path = _write_temp_log("garbage\n")
        try:
            result = compute_summary(path)
        finally:
            os.remove(path)

        text = render_summary_text(result)
        self.assertIn("First timestamp: N/A", text)
        self.assertIn("Last timestamp:  N/A", text)
        self.assertIn("(none)", text)


if __name__ == "__main__":
    unittest.main()
