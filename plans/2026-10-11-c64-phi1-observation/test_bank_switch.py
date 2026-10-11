"""Require complete native bank observations and reject false passes."""

from __future__ import annotations

import gzip
import json
import unittest
from pathlib import Path

from bank_switch import verify


class BankSwitchGuards(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = json.loads(
            gzip.decompress(
                Path(__file__).with_name("bank-switch-comparison.json.gz").read_bytes()
            )
        )["rows"]

    def test_native_capture(self) -> None:
        result = verify(self.rows)
        self.assertEqual(result["samples"], 3840)
        self.assertEqual(result["stale_bank_rejections"], 2880)

    def test_empty_capture(self) -> None:
        with self.assertRaises(AssertionError):
            verify([])

    def test_missing_row(self) -> None:
        self.rows.pop()
        with self.assertRaises(AssertionError):
            verify(self.rows)

    def test_duplicate_row(self) -> None:
        self.rows[-1] = self.rows[0]
        with self.assertRaises(AssertionError):
            verify(self.rows)

    def test_short_capture(self) -> None:
        self.rows[0]["samples"].pop()
        with self.assertRaises(AssertionError):
            verify(self.rows)

    def test_wrong_byte_even_with_matching_trace_and_claimed_success(self) -> None:
        self.rows[0]["samples"][0] = 0xFF
        self.rows[0]["trace"][0][2] = "FF"
        self.rows[0]["differences"] = 0
        with self.assertRaises(AssertionError):
            verify(self.rows)

    def test_trace_disagrees(self) -> None:
        self.rows[0]["trace"][0][2] = "FF"
        with self.assertRaises(AssertionError):
            verify(self.rows)

    def test_no_completion(self) -> None:
        self.rows[0]["sentinel"] = 0
        with self.assertRaises(AssertionError):
            verify(self.rows)

    def test_empty_trace(self) -> None:
        self.rows[0]["trace"] = []
        with self.assertRaises(AssertionError):
            verify(self.rows)

    def test_invalid_byte(self) -> None:
        self.rows[0]["samples"][0] = 256
        with self.assertRaises(AssertionError):
            verify(self.rows)


if __name__ == "__main__":
    unittest.main()
