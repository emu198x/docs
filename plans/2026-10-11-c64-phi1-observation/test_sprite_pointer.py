"""Falsify stale/eager pointers, mixed rows, MC resets and unmeasured timing."""

from __future__ import annotations

import csv
import io
import json
import unittest
import zipfile
from pathlib import Path

from verify_fetch_trace import verify_rows
from verify_sprite_pointer import (
    verify_archive,
    verify_case,
    verify_controls,
    verify_coverage,
)

ARCHIVE = Path(__file__).with_name("pointer-native.zip")


class SpritePointerGuards(unittest.TestCase):
    def setUp(self) -> None:
        with zipfile.ZipFile(ARCHIVE) as archive:
            self.cases = json.loads(archive.read("capture.json"))["rows"]
            self.case = next(
                c
                for c in self.cases
                if c["model"] == "pal"
                and c["bank"] == 0
                and not c["reverse"]
                and c["delay"] == 18
            )
            name = "pal-bank0-sprite0-delay18-phase0-reverse0"
            self.rows = list(
                csv.reader(io.StringIO(archive.read(name + ".csv").decode()))
            )
            self.log = archive.read(name + ".log").decode()

    def verify(self) -> dict:
        return verify_case(self.case, self.rows, self.log)

    def change_phi1(self, index: int, value: int) -> None:
        self.rows[index][6] = str(value)
        self.rows[index + 1][6] = self.rows[index + 1][10] = str(value)
        for row in self.rows[index + 2 :]:
            if row[0] == "L1":
                break
            row[10] = str(value)

    def test_all_native_boundaries(self) -> None:
        result = verify_archive(ARCHIVE)
        self.assertEqual(result["sprite_bytes"], 5040)
        self.assertEqual(result["stalled_pairs"], 40)
        self.assertEqual(result["boundaries"], {"before": 40, "after": 40})

    def test_dma_disabled_controls(self) -> None:
        result = verify_controls(ARCHIVE.with_name("pointer-controls.zip"))
        self.assertEqual(result["cases"], 10)
        self.assertEqual(result["unstalled_pairs"], 5)

    def test_stale_pointer(self) -> None:
        index = next(
            i
            for i, r in enumerate(self.rows)
            if r[0] == "P1" and r[4] == "2040" and r[6] == "129"
        )
        self.change_phi1(index, 128)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "CPU-clock pointer selection"):
            self.verify()

    def test_eager_pointer(self) -> None:
        index = next(
            i
            for i, r in enumerate(self.rows)
            if r[0] == "P1" and r[4] == "2040" and r[6] == "128"
        )
        self.change_phi1(index, 129)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "CPU-clock pointer selection"):
            self.verify()

    def test_mixed_row_sources(self) -> None:
        row = next(r for r in self.rows if r[0] == "P2" and int(r[4]) == 0x2040 + 32)
        row[4] = row[5] = str(0x2000 + 32)
        row[6] = str(self.case["ram"][32])
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "latched pointer/MC source"):
            self.verify()

    def test_mc_reset_when_pointer_changes(self) -> None:
        row = next(r for r in self.rows if r[0] == "P2" and int(r[4]) == 0x2040 + 30)
        row[4] = row[5] = str(0x2040)
        row[6] = str(self.case["ram"][64])
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "latched pointer/MC source"):
            self.verify()

    def test_wrong_byte(self) -> None:
        row = next(r for r in self.rows if r[0] == "P2")
        row[6] = str(int(row[6]) ^ 1)
        with self.assertRaisesRegex(AssertionError, "source byte"):
            self.verify()

    def test_wrong_bank(self) -> None:
        row = next(r for r in self.rows if r[0] == "P2")
        row[5] = str(int(row[5]) + 0x4000)
        with self.assertRaisesRegex(AssertionError, "physical bank"):
            self.verify()

    def test_missing_data_byte(self) -> None:
        self.rows.remove(next(r for r in self.rows if r[0] == "P2"))
        self.rows[-1] = ["END", str(len(self.rows) - 3)]
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "byte sequence"):
            self.verify()

    def test_missing_cpu_write(self) -> None:
        self.log = self.log.replace("Trace store 07f8", "removed", 1)
        with self.assertRaisesRegex(AssertionError, "CPU store coverage"):
            self.verify()

    def test_fake_cpu_clock(self) -> None:
        self.case["writes"][-1][3] += 1
        with self.assertRaisesRegex(AssertionError, "CPU store coverage"):
            self.verify()

    def test_missing_completion(self) -> None:
        self.log = self.log.replace("Stop on store d7ff", "removed")
        with self.assertRaisesRegex(AssertionError, "completion event"):
            self.verify()

    def test_wrong_source_ram(self) -> None:
        self.case["ram"][64] ^= 1
        with self.assertRaisesRegex(AssertionError, "source RAM"):
            self.verify()

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(AssertionError, "case coverage"):
            verify_coverage(self.cases[:-1])

    def test_duplicate_case(self) -> None:
        self.cases[-1] = self.cases[0]
        with self.assertRaisesRegex(AssertionError, "case coverage"):
            verify_coverage(self.cases)


if __name__ == "__main__":
    unittest.main()
