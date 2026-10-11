"""Falsification controls on complete original native sprite captures."""

from __future__ import annotations

import csv
import io
import json
import unittest
import zipfile
from pathlib import Path

from verify_fetch_trace import verify_rows
from verify_sprite_fetch import verify_archive, verify_case, verify_coverage

ARCHIVE = Path(__file__).with_name("sprite-native.zip")


class SpriteFetchGuards(unittest.TestCase):
    def setUp(self) -> None:
        with zipfile.ZipFile(ARCHIVE) as archive:
            self.cases = json.loads(archive.read("capture.json"))["rows"]
            self.case = next(
                c
                for c in self.cases
                if (c["model"], c["bank"], c["mask"]) == ("pal", 0, 255)
            )
            self.rows = list(
                csv.reader(io.StringIO(archive.read("pal-bank0-maskff.csv").decode()))
            )
        self.p2 = next(r for r in self.rows if r[0] == "P2")

    def recount(self) -> None:
        self.rows[-1] = ["END", str(len(self.rows) - 3)]

    def test_full_native_matrix(self) -> None:
        result = verify_archive(ARCHIVE)
        self.assertEqual(result["cases"], 200)
        self.assertEqual(result["sprite_bytes"], 20_160)
        self.assertEqual(result["P1"], 6720)
        self.assertEqual(result["P2"], 13_440)

    def test_empty_capture(self) -> None:
        with self.assertRaises(AssertionError):
            verify_rows([], 63)

    def test_missing_footer(self) -> None:
        with self.assertRaises(AssertionError):
            verify_case(self.case, self.rows[:-1])

    def test_empty_record(self) -> None:
        self.rows[10] = []
        with self.assertRaisesRegex(AssertionError, "empty record"):
            verify_case(self.case, self.rows)

    def test_wrong_footer_count(self) -> None:
        self.rows[-1][1] = "0"
        with self.assertRaises(AssertionError):
            verify_case(self.case, self.rows)

    def test_missing_clock(self) -> None:
        del self.rows[50:52]  # A complete P1/L1 pair, outside sprite DMA.
        self.recount()
        with self.assertRaisesRegex(AssertionError, "missing/duplicate clock"):
            verify_case(self.case, self.rows)

    def test_duplicate_clock(self) -> None:
        self.rows[52:52] = [r.copy() for r in self.rows[50:52]]
        self.recount()
        with self.assertRaisesRegex(AssertionError, "missing/duplicate clock"):
            verify_case(self.case, self.rows)

    def test_wrong_bank(self) -> None:
        self.p2[5] = str(int(self.p2[5]) + 0x4000)
        with self.assertRaisesRegex(AssertionError, "wrong physical bank"):
            verify_case(self.case, self.rows)

    def test_wrong_source_byte(self) -> None:
        self.p2[6] = str(int(self.p2[6]) ^ 1)
        with self.assertRaisesRegex(AssertionError, "sprite source byte"):
            verify_case(self.case, self.rows)

    def test_wrong_byte_position(self) -> None:
        for column in [4, 5]:
            self.p2[column] = str(int(self.p2[column]) + 1)
        with self.assertRaisesRegex(AssertionError, "sprite byte position"):
            verify_case(self.case, self.rows)

    def test_shifted_phi2(self) -> None:
        self.p2[3] = str((int(self.p2[3]) + 1) % 63)
        with self.assertRaisesRegex(AssertionError, "Phi2 phase"):
            verify_case(self.case, self.rows)

    def test_phi2_overwrites_phi1(self) -> None:
        self.assertNotEqual(self.p2[6], self.p2[10])
        self.p2[10] = self.p2[6]
        with self.assertRaisesRegex(AssertionError, "retained Phi1 changed"):
            verify_case(self.case, self.rows)

    def test_phi1_not_latched(self) -> None:
        self.rows[2][6] = str(int(self.rows[2][6]) ^ 1)
        with self.assertRaisesRegex(AssertionError, "wrong/missing Phi1 fetch"):
            verify_case(self.case, self.rows)

    def test_missing_dma_byte_despite_valid_structure(self) -> None:
        self.rows.remove(self.p2)
        self.recount()
        verify_rows(self.rows, 63)  # Structure alone cannot prove sprite coverage.
        with self.assertRaisesRegex(AssertionError, "DMA byte coverage"):
            verify_case(self.case, self.rows)

    def test_wrong_pointer_address(self) -> None:
        row = next(
            r for r in self.rows[2:-1] if r[0] == "P1" and int(r[9]) & 0xE00 == 0x600
        )
        for column in [4, 5]:
            row[column] = str(int(row[column]) + 1)
        with self.assertRaisesRegex(AssertionError, "pointer source"):
            verify_case(self.case, self.rows)

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(AssertionError, "case coverage"):
            verify_coverage(self.cases[:-1])

    def test_duplicate_case(self) -> None:
        self.cases[-1] = self.cases[0]
        with self.assertRaisesRegex(AssertionError, "case coverage"):
            verify_coverage(self.cases)

    def test_wrong_ram(self) -> None:
        self.case["ram"][0] ^= 1
        with self.assertRaisesRegex(AssertionError, "source RAM"):
            verify_case(self.case, self.rows)

    def test_line_number_corruption(self) -> None:
        for row in self.rows[2:-1]:
            row[2] = str(int(row[2]) + 1)
        with self.assertRaisesRegex(AssertionError, "incomplete line interval"):
            verify_case(self.case, self.rows)


if __name__ == "__main__":
    unittest.main()
