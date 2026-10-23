import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logscope.grep import compute_grep, parse_since, render_grep_text, validate_level


def _write_temp_log(content: str) -> str:
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8")
    handle.write(content)
    handle.close()
    return handle.name


SAMPLE_CONTENT = (
    "2026-10-01 09:00:00 INFO Application started\n"
    "2026-10-01 09:01:00 WARN Slow response detected\n"
    "2026-10-01 09:02:00 ERROR Database connection failed\n"
    "malformed line without timestamp and level\n"
    "2026-10-01 09:15:00 ERROR Timeout while calling payment API\n"
    "2026-10-01 09:20:00 INFO Health check passed\n"
    "2026-10-01 BADTS ERROR broken timestamp example\n"
)


class ParseSinceTests(unittest.TestCase):
    def test_valid_since(self):
        dt = parse_since("2026-10-01 09:00")
        self.assertEqual(dt, datetime(2026, 10, 1, 9, 0))

    def test_invalid_since_raises(self):
        with self.assertRaises(ValueError):
            parse_since("not-a-date")


class ValidateLevelTests(unittest.TestCase):
    def test_none_passthrough(self):
        self.assertIsNone(validate_level(None))

    def test_valid_level(self):
        self.assertEqual(validate_level("ERROR"), "ERROR")

    def test_invalid_level_raises(self):
        with self.assertRaises(ValueError):
            validate_level("DEBUG")


class ComputeGrepTests(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_log(SAMPLE_CONTENT)

    def tearDown(self):
        os.remove(self.path)

    def test_no_filters_returns_all_valid_records(self):
        result = compute_grep(self.path)
        self.assertEqual(len(result.matches), 5)
        self.assertEqual(result.malformed_count, 2)

    def test_level_filter(self):
        result = compute_grep(self.path, level="ERROR")
        self.assertEqual(len(result.matches), 2)
        self.assertTrue(all(record.level == "ERROR" for record in result.matches))

    def test_since_filter_boundary_inclusive(self):
        result = compute_grep(self.path, since="2026-10-01 09:15")
        timestamps = [record.timestamp for record in result.matches]
        self.assertIn(datetime(2026, 10, 1, 9, 15, 0), timestamps)
        self.assertNotIn(datetime(2026, 10, 1, 9, 2, 0), timestamps)

    def test_combined_level_and_since_filters(self):
        result = compute_grep(self.path, level="ERROR", since="2026-10-01 09:10")
        self.assertEqual(len(result.matches), 1)
        self.assertEqual(result.matches[0].message, "Timeout while calling payment API")

    def test_malformed_lines_counted_regardless_of_filters(self):
        result = compute_grep(self.path, level="INFO")
        self.assertEqual(result.malformed_count, 2)

    def test_no_match_scenario(self):
        result = compute_grep(self.path, level="ERROR", since="2026-10-02 00:00")
        self.assertEqual(result.matches, [])
        self.assertEqual(result.malformed_count, 2)

    def test_invalid_level_raises(self):
        with self.assertRaises(ValueError):
            compute_grep(self.path, level="CRITICAL")

    def test_invalid_since_raises(self):
        with self.assertRaises(ValueError):
            compute_grep(self.path, since="garbage")


class RenderGrepTextTests(unittest.TestCase):
    def test_render_includes_raw_lines_and_malformed_count(self):
        path = _write_temp_log(SAMPLE_CONTENT)
        try:
            result = compute_grep(path, level="ERROR")
        finally:
            os.remove(path)

        text = render_grep_text(result)
        self.assertIn("Database connection failed", text)
        self.assertIn("Malformed lines skipped: 2", text)


if __name__ == "__main__":
    unittest.main()
