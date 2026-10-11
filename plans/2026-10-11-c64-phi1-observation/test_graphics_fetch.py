"""Falsify incorrect modes, matrix retention, counters and phase ownership."""

from __future__ import annotations

import csv
import io
import json
import unittest
import zipfile
from pathlib import Path

from verify_fetch_trace import verify_rows
from verify_graphics_fetch import stem, verify_archive, verify_case, verify_coverage

ARCHIVE = Path(__file__).with_name("graphics-native.zip")


class GraphicsFetchGuards(unittest.TestCase):
    def setUp(self) -> None:
        self.load(0)

    def load(self, mode: int) -> None:
        with zipfile.ZipFile(ARCHIVE) as archive:
            self.cases = json.loads(archive.read("capture.json"))["rows"]
            self.case = next(
                c
                for c in self.cases
                if c["model"] == "pal" and c["bank"] == 0 and c["mode"] == mode
            )
            name = stem(self.case)
            self.rows = list(
                csv.reader(io.StringIO(archive.read(name + ".csv").decode()))
            )
            self.matrix = archive.read(name + "-matrix.bin")
            self.graphics = archive.read(name + "-graphics.bin")
            self.log = archive.read(name + ".log").decode()

    def record(self, kind: str, line: int = 59, cycle: int = 15) -> list[str]:
        return next(
            r
            for r in self.rows[2:-1]
            if r[0] == kind and int(r[2]) == line and int(r[3]) == cycle
        )

    def verify(self) -> dict:
        return verify_case(self.case, self.rows, self.matrix, self.graphics, self.log)

    def coherent_data(self, row: list[str], data: int) -> None:
        """Change the fetched byte and its retained latch without breaking pairing."""
        row[6] = str(data)
        after = False
        for candidate in self.rows[self.rows.index(row) + 1 : -1]:
            if candidate[0] == "L1":
                if after:
                    break
                candidate[6] = str(data)
                after = True
            candidate[10] = str(data)

    def test_all_modes_models_banks(self) -> None:
        result = verify_archive(ARCHIVE)
        self.assertEqual(result["active_graphics"], 160000)
        self.assertEqual(result["retained_matrix_graphics"], 134400)
        self.assertEqual(result["matrix_bytes"], 25600)

    def test_text_uses_matrix_code_not_column(self) -> None:
        row = self.record("P1", 51)
        row[4] = row[5] = str(0x2000)
        with self.assertRaisesRegex(AssertionError, "graphics address"):
            self.verify()

    def test_bitmap_uses_video_counter_not_character_code(self) -> None:
        self.load(2)
        row = self.record("P1", 51)
        row[4] = row[5] = str(0x2000 + self.matrix[0] * 8)
        with self.assertRaisesRegex(AssertionError, "graphics address"):
            self.verify()

    def test_ecm_masks_character_address_bits(self) -> None:
        self.load(4)
        row = next(
            r
            for r in self.rows[2:-1]
            if r[0] == "P1" and r[2] == "51" and int(r[3]) >= 20 and int(r[3]) <= 54
        )
        row[4] = row[5] = str(int(row[4]) | 0x200)
        with self.assertRaisesRegex(AssertionError, "graphics address"):
            self.verify()

    def test_invalid_bitmap_ecm_still_masks_address(self) -> None:
        self.load(6)
        row = self.record("P1", 67)
        row[4] = row[5] = str(int(row[4]) | 0x200)
        with self.assertRaisesRegex(AssertionError, "graphics address"):
            self.verify()

    def test_row_counter_advances_between_badlines(self) -> None:
        row = self.record("P1", 52)
        row[4] = row[5] = str(int(row[4]) - 1)
        with self.assertRaisesRegex(AssertionError, "graphics address"):
            self.verify()

    def test_next_badline_replaces_matrix_row(self) -> None:
        row = self.record("P1", 59)
        row[4] = row[5] = str(0x2000 + self.matrix[0] * 8)
        with self.assertRaisesRegex(AssertionError, "graphics address"):
            self.verify()

    def test_non_badline_retains_matrix_row(self) -> None:
        row = self.record("P1", 60)
        row[4] = row[5] = str(0x2001 + self.matrix[80] * 8)
        with self.assertRaisesRegex(AssertionError, "graphics address"):
            self.verify()

    def test_idle_ecm_uses_masked_idle_address(self) -> None:
        self.load(5)
        row = self.record("P1", 50)
        row[4] = row[5] = str(0x3FFF)
        with self.assertRaisesRegex(AssertionError, "graphics address"):
            self.verify()

    def test_coherent_wrong_graphics_byte(self) -> None:
        row = self.record("P1")
        self.coherent_data(row, int(row[6]) ^ 1)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "graphics source byte"):
            self.verify()

    def test_wrong_graphics_bank(self) -> None:
        row = self.record("P1")
        row[5] = str(int(row[5]) + 0x4000)
        with self.assertRaisesRegex(AssertionError, "graphics physical bank"):
            self.verify()

    def test_matrix_data_from_wrong_source(self) -> None:
        row = self.record("P2")
        row[6] = str(int(row[6]) ^ 1)
        with self.assertRaisesRegex(AssertionError, "matrix source byte"):
            self.verify()

    def test_missing_matrix_column(self) -> None:
        self.rows.remove(self.record("P2"))
        self.rows[-1][1] = str(len(self.rows) - 3)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "matrix column coverage"):
            self.verify()

    def test_matrix_phase_is_current_cycle(self) -> None:
        row = self.record("P2")
        row[3] = str(int(row[3]) - 1)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "absolute fetch cycle"):
            self.verify()

    def test_matrix_cannot_overwrite_phi1_latch(self) -> None:
        row = self.record("P2")
        self.assertNotEqual(row[6], row[10])
        row[10] = row[6]
        with self.assertRaisesRegex(AssertionError, "retained Phi1"):
            self.verify()

    def test_missing_graphics_slot(self) -> None:
        row = self.record("P1")
        row[9] = str(int(row[9]) & ~0x0E00)
        with self.assertRaisesRegex(AssertionError, "graphics slot identity"):
            self.verify()

    def test_wrong_matrix_address(self) -> None:
        row = self.record("P2")
        row[4] = str(int(row[4]) - 40)
        with self.assertRaisesRegex(AssertionError, "matrix address sequence"):
            self.verify()

    def test_missing_completion(self) -> None:
        self.log = self.log.replace("Stop on store d7ff", "removed")
        with self.assertRaisesRegex(AssertionError, "completion event"):
            self.verify()

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(AssertionError, "graphics case coverage"):
            verify_coverage(self.cases[:-1])

    def test_duplicate_case(self) -> None:
        self.cases[-1] = self.cases[0]
        with self.assertRaisesRegex(AssertionError, "graphics case coverage"):
            verify_coverage(self.cases)

    def test_no_cases(self) -> None:
        with self.assertRaisesRegex(AssertionError, "graphics case coverage"):
            verify_coverage([])


if __name__ == "__main__":
    unittest.main()
