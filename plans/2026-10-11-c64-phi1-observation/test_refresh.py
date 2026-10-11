"""Coverage and falsification guards for refresh-address observations."""

from __future__ import annotations

import gzip
import json
import unittest
from pathlib import Path

from verify_refresh import verify


class RefreshGuards(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(
            gzip.decompress(
                Path(__file__).with_name("refresh-comparison.json.gz").read_bytes()
            )
        )

    def test_observations_and_counter_mutations(self) -> None:
        result = verify(self.data)
        self.assertEqual(result["refresh_samples"], 300)
        self.assertEqual(
            result["counter_mutation_mismatches"],
            {
                "predecrement": 300,
                "increment": 280,
                "reset_each_line": 280,
                "omit_frame_reset": 60,
            },
        )

    def test_empty_capture_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            verify({"rows": []})

    def test_missing_row_rejected(self) -> None:
        self.data["rows"].pop()
        with self.assertRaises(AssertionError):
            verify(self.data)

    def test_duplicate_row_rejected(self) -> None:
        self.data["rows"][-1] = self.data["rows"][0]
        with self.assertRaises(AssertionError):
            verify(self.data)

    def test_wrong_byte_rejected(self) -> None:
        self.data["rows"][0]["refresh"][0]["actual"] ^= 1
        with self.assertRaises(AssertionError):
            verify(self.data)

    def test_wrong_address_rejected(self) -> None:
        self.data["rows"][0]["refresh"][0]["address"] ^= 1
        with self.assertRaises(AssertionError):
            verify(self.data)

    def test_short_page_rejected(self) -> None:
        self.data["rows"][0]["refresh_page"].pop()
        with self.assertRaises(AssertionError):
            verify(self.data)

    def test_zero_trace_rejected(self) -> None:
        self.data["rows"][0]["trace_samples"] = 0
        with self.assertRaises(AssertionError):
            verify(self.data)

    def test_wrong_model_length_rejected(self) -> None:
        self.data["rows"][0]["cycles"] = 0
        self.data["rows"][0]["trace_samples"] = 0
        with self.assertRaises(AssertionError):
            verify(self.data)


if __name__ == "__main__":
    unittest.main()
