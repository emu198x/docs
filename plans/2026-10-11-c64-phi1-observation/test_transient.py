"""Require complete native pixel evidence and honest CPU-probe failures."""

from __future__ import annotations

import gzip
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from capture import digest
from run_transient_probe import analyse
from verify_transient import verify

ROOT = Path(__file__).parent


class TransientGuards(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(
            gzip.decompress((ROOT / "transient-native/comparison.json.gz").read_bytes())
        )
        self.log = (ROOT / "transient-run.log").read_text()

    def test_native_bit_predictions_and_controls(self) -> None:
        result = verify(self.data, ROOT / "transient-native")
        self.assertEqual(result["captures"], 70)
        self.assertEqual(result["no_transient_controls"], 15)
        self.assertEqual(
            [r["bank3_pixels"] for r in result["effects"]],
            [6544, 6544, 6664, 6664, 6544],
        )

    def test_missing_capture(self) -> None:
        self.data["captures"].pop()
        with self.assertRaises(AssertionError):
            verify(self.data, ROOT / "transient-native")

    def test_duplicate_capture(self) -> None:
        self.data["captures"][-1] = self.data["captures"][0]
        with self.assertRaises(AssertionError):
            verify(self.data, ROOT / "transient-native")

    def test_fabricated_zero_difference_count(self) -> None:
        self.data["comparisons"][1]["differences"] = 0
        with self.assertRaises(AssertionError):
            verify(self.data, ROOT / "transient-native")

    def test_wrong_marker_even_with_consistent_image_hash_and_difference_array(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="c64-transient-negative-") as temp:
            root = Path(temp)
            for image in (ROOT / "transient-native").glob("*.png"):
                shutil.copyfile(image, root / image.name)
            stem = "pal-1-2-markeraa-glue1"
            target = root / (stem + ".png")
            shutil.copyfile(root / "pal-1-2-marker55-glue1.png", target)
            row = next(r for r in self.data["captures"] if r["stem"] == stem)
            row["image_sha256"] = digest(target)
            comparisons = self.data["comparisons"]
            source = next(
                r
                for r in comparisons
                if r["model"] == "pal" and r["pair"] == [1, 2] and r["marker"] == 85
            )
            wrong = next(
                r
                for r in comparisons
                if r["model"] == "pal" and r["pair"] == [1, 2] and r["marker"] == 170
            )
            wrong["pixel_indices"] = source["pixel_indices"]
            wrong["differences"] = source["differences"]
            with self.assertRaises(AssertionError):
                verify(self.data, root)

    def test_retained_red_cpu_probe(self) -> None:
        self.assertEqual(analyse(self.log, 101)["failed"], 2)

    def test_missing_cpu_rows(self) -> None:
        with self.assertRaises(AssertionError):
            analyse("", 101)

    def test_duplicate_cpu_row(self) -> None:
        with self.assertRaises(AssertionError):
            analyse(self.log + "\nBANK_TRANSIENT|pal|129792|0|0", 101)

    def test_cpu_false_success_exit(self) -> None:
        with self.assertRaises(AssertionError):
            analyse(self.log, 0)

    def test_wrong_board_expectation(self) -> None:
        with self.assertRaises(AssertionError):
            analyse(
                self.log.replace(
                    "BANK_TRANSIENT|pal|129792|0|0", "BANK_TRANSIENT|pal|129792|0|1"
                ),
                101,
            )


if __name__ == "__main__":
    unittest.main()
