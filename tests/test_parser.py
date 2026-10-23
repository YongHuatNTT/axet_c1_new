import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logscope.parser import LogRecord, iter_log_records, parse_line


class ParseLineTests(unittest.TestCase):
    def test_valid_info_line(self):
        record = parse_line("2026-10-01 09:00:00 INFO Application started")
        self.assertIsInstance(record, LogRecord)
        self.assertEqual(record.timestamp, datetime(2026, 10, 1, 9, 0, 0))
        self.assertEqual(record.level, "INFO")
        self.assertEqual(record.message, "Application started")

    def test_valid_error_line_with_spaces_in_message(self):
        record = parse_line("2026-10-01 09:02:00 ERROR Database connection failed")
        self.assertIsNotNone(record)
        self.assertEqual(record.level, "ERROR")
        self.assertEqual(record.message, "Database connection failed")

    def test_invalid_timestamp_is_malformed(self):
        record = parse_line("2026-10-01 BADTS ERROR broken timestamp example")
        self.assertIsNone(record)

    def test_invalid_level_is_malformed(self):
        record = parse_line("2026-10-01 09:00:00 DEBUG not a valid level")
        self.assertIsNone(record)

    def test_missing_message_is_malformed(self):
        record = parse_line("2026-10-01 09:00:00 INFO")
        self.assertIsNone(record)

    def test_completely_unstructured_line_is_malformed(self):
        record = parse_line("malformed line without timestamp and level")
        self.assertIsNone(record)

    def test_blank_line_returns_none(self):
        self.assertIsNone(parse_line(""))
        self.assertIsNone(parse_line("   "))


class IterLogRecordsTests(unittest.TestCase):
    def _write_temp_log(self, content: str) -> str:
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        )
        handle.write(content)
        handle.close()
        return handle.name

    def test_streams_records_and_marks_malformed(self):
        content = (
            "2026-10-01 09:00:00 INFO Application started\n"
            "malformed line without timestamp and level\n"
            "2026-10-01 09:02:00 ERROR Database connection failed\n"
            "\n"
            "2026-10-01 BADTS ERROR broken timestamp example\n"
        )
        path = self._write_temp_log(content)
        try:
            results = list(iter_log_records(path))
        finally:
            os.remove(path)

        self.assertEqual(len(results), 4)
        record_0, raw_0 = results[0]
        self.assertIsNotNone(record_0)
        self.assertEqual(record_0.level, "INFO")

        record_1, raw_1 = results[1]
        self.assertIsNone(record_1)
        self.assertEqual(raw_1, "malformed line without timestamp and level")

        record_2, _ = results[2]
        self.assertIsNotNone(record_2)
        self.assertEqual(record_2.level, "ERROR")

        record_3, _ = results[3]
        self.assertIsNone(record_3)

        malformed_count = sum(1 for record, _ in results if record is None)
        self.assertEqual(malformed_count, 2)

    def test_blank_lines_are_not_counted_as_malformed(self):
        content = "\n\n2026-10-01 09:00:00 INFO Application started\n\n"
        path = self._write_temp_log(content)
        try:
            results = list(iter_log_records(path))
        finally:
            os.remove(path)

        self.assertEqual(len(results), 1)
        record, _ = results[0]
        self.assertIsNotNone(record)


if __name__ == "__main__":
    unittest.main()
