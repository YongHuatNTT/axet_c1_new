import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logscope.timeline import (
    compute_timeline,
    floor_timestamp,
    parse_bucket_interval,
    render_timeline_text,
)


def _write_temp_log(content: str) -> str:
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8")
    handle.write(content)
    handle.close()
    return handle.name


class ParseBucketIntervalTests(unittest.TestCase):
    def test_minutes(self):
        self.assertEqual(parse_bucket_interval("15m"), timedelta(minutes=15))

    def test_hours(self):
        self.assertEqual(parse_bucket_interval("1h"), timedelta(hours=1))

    def test_seconds(self):
        self.assertEqual(parse_bucket_interval("30s"), timedelta(seconds=30))

    def test_invalid_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_bucket_interval("15x")

    def test_invalid_number_raises(self):
        with self.assertRaises(ValueError):
            parse_bucket_interval("abcm")

    def test_zero_value_raises(self):
        with self.assertRaises(ValueError):
            parse_bucket_interval("0m")


class FloorTimestampTests(unittest.TestCase):
    def test_floors_to_bucket_start_before_boundary(self):
        ts = datetime(2026, 10, 1, 9, 14, 59)
        floored = floor_timestamp(ts, timedelta(minutes=15))
        self.assertEqual(floored, datetime(2026, 10, 1, 9, 0, 0))

    def test_floors_to_bucket_start_at_boundary(self):
        ts = datetime(2026, 10, 1, 9, 15, 0)
        floored = floor_timestamp(ts, timedelta(minutes=15))
        self.assertEqual(floored, datetime(2026, 10, 1, 9, 15, 0))


ERROR_SAMPLE = (
    "2026-10-01 09:00:00 INFO Application started\n"
    "2026-10-01 09:02:00 ERROR Database connection failed\n"
    "2026-10-01 09:04:00 ERROR Database connection failed\n"
    "malformed line without timestamp and level\n"
    "2026-10-01 09:14:59 ERROR Timeout while calling payment API\n"
    "2026-10-01 09:15:00 ERROR Disk space critically low\n"
    "2026-10-01 09:20:00 ERROR Disk space critically low\n"
    "2026-10-01 BADTS ERROR broken timestamp example\n"
)


class ComputeTimelineTests(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_log(ERROR_SAMPLE)

    def tearDown(self):
        os.remove(self.path)

    def test_groups_errors_into_15m_buckets(self):
        result = compute_timeline(self.path, "15m")
        bucket_map = {start: count for start, count in result.buckets}
        self.assertEqual(bucket_map[datetime(2026, 10, 1, 9, 0, 0)], 3)
        self.assertEqual(bucket_map[datetime(2026, 10, 1, 9, 15, 0)], 2)

    def test_ignores_non_error_levels(self):
        result = compute_timeline(self.path, "15m")
        total_errors = sum(count for _start, count in result.buckets)
        self.assertEqual(total_errors, 5)

    def test_malformed_count(self):
        result = compute_timeline(self.path, "15m")
        self.assertEqual(result.malformed_count, 2)

    def test_buckets_are_chronologically_sorted(self):
        result = compute_timeline(self.path, "15m")
        starts = [start for start, _count in result.buckets]
        self.assertEqual(starts, sorted(starts))

    def test_no_errors_returns_empty_buckets(self):
        path = _write_temp_log("2026-10-01 09:00:00 INFO Application started\n")
        try:
            result = compute_timeline(path, "15m")
        finally:
            os.remove(path)
        self.assertEqual(result.buckets, [])
        self.assertEqual(result.malformed_count, 0)


class RenderTimelineTextTests(unittest.TestCase):
    def test_render_includes_bucket_labels_and_counts(self):
        path = _write_temp_log(ERROR_SAMPLE)
        try:
            result = compute_timeline(path, "15m")
        finally:
            os.remove(path)

        text = render_timeline_text(result)
        self.assertIn("2026-10-01 09:00", text)
        self.assertIn("2026-10-01 09:15", text)
        self.assertIn("Malformed lines: 2", text)

    def test_render_handles_no_errors(self):
        path = _write_temp_log("2026-10-01 09:00:00 INFO Application started\n")
        try:
            result = compute_timeline(path, "15m")
        finally:
            os.remove(path)

        text = render_timeline_text(result)
        self.assertIn("no ERROR records found", text)


if __name__ == "__main__":
    unittest.main()
