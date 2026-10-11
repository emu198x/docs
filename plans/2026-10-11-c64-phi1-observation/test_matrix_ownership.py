"""Falsify late matrix ownership, address progression and retained consumption."""

from __future__ import annotations

import csv
import io
import json
import re
import unittest
import zipfile
from pathlib import Path

from bank_phase import EVENT
from matrix_ownership import stem
from verify_fetch_trace import verify_rows
from verify_matrix_ownership import verify_archive, verify_case, verify_coverage

ARCHIVE = Path(__file__).with_name("matrix-ownership-native.zip")


class MatrixOwnershipGuards(unittest.TestCase):
    def setUp(self) -> None:
        self.load()

    def load(self, delay: int = 0, phase: int = 0, force: bool = True) -> None:
        with zipfile.ZipFile(ARCHIVE) as archive:
            self.cases = json.loads(archive.read("capture.json"))["rows"]
            self.case = next(
                c
                for c in self.cases
                if c["model"] == "pal"
                and c["bank"] == 0
                and c["delay"] == delay
                and c["phase"] == phase
                and c["force"] == force
            )
            n = stem(self.case)
            self.rows = list(csv.reader(io.StringIO(archive.read(n + ".csv").decode())))
            self.matrix = archive.read(n + "-matrix.bin")
            self.graphics = archive.read(n + "-graphics.bin")
            self.log = archive.read(n + ".log").decode()

    def verify(self) -> dict:
        return verify_case(self.case, self.rows, self.matrix, self.graphics, self.log)

    def invalid(self) -> list[str]:
        return next(r for r in self.rows[2:-1] if r[0] == "MI")

    def valid(self) -> list[str]:
        return next(r for r in self.rows[2:-1] if r[0] == "P2" and r[2] == "60")

    def test_full_model_bank_control_matrix(self) -> None:
        result = verify_archive(ARCHIVE)
        self.assertEqual(result["cases"], 415)
        self.assertEqual(result["controls"], 100)
        self.assertEqual(result["boundary_cases"], 160)
        self.assertEqual(result["consumed_graphics"], 415 * 80)
        self.assertEqual(result["invalid_matrix"], 633)

    def test_invalid_read_cannot_be_ram_fetch(self) -> None:
        r = self.invalid()
        r[0] = "P2"
        r[5] = r[4]
        r[6] = str(self.matrix[int(r[4]) - 0x400])
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "matrix ownership countdown"):
            self.verify()

    def test_countdown_cannot_be_shortened(self) -> None:
        r = self.invalid()
        r[8] = "2"
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "matrix ownership countdown"):
            self.verify()

    def test_valid_read_cannot_stay_disconnected(self) -> None:
        r = self.valid()
        r[0] = "MI"
        r[5] = "-1"
        r[6] = "255"
        r[8] = "1"
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "matrix ownership countdown"):
            self.verify()

    def test_invalid_byte_is_ff(self) -> None:
        self.invalid()[6] = "254"
        with self.assertRaises(AssertionError):
            self.verify()

    def test_missing_invalid_attempt(self) -> None:
        self.rows.remove(self.invalid())
        self.rows[-1][1] = str(len(self.rows) - 3)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "complete matrix sequence"):
            self.verify()

    def test_first_valid_byte_cannot_be_missing(self) -> None:
        self.rows.remove(self.valid())
        self.rows[-1][1] = str(len(self.rows) - 3)
        with self.assertRaisesRegex(AssertionError, "complete matrix sequence"):
            self.verify()

    def test_disconnected_attempt_advances_address(self) -> None:
        r = next(r for r in self.rows[2:-1] if r[0] == "MI" and r[8] == "2")
        r[4] = str(int(r[4]) - 1)
        with self.assertRaisesRegex(AssertionError, "matrix address sequence"):
            self.verify()

    def test_ram_data_has_independent_source(self) -> None:
        r = self.valid()
        r[6] = str(int(r[6]) ^ 1)
        with self.assertRaisesRegex(AssertionError, "matrix RAM access"):
            self.verify()

    def test_wrong_physical_bank(self) -> None:
        r = self.valid()
        r[5] = str(int(r[5]) + 0x4000)
        with self.assertRaisesRegex(AssertionError, "matrix RAM access"):
            self.verify()

    def test_invalid_attempt_preserves_phi1(self) -> None:
        r = self.invalid()
        r[10] = str(int(r[10]) ^ 1)
        with self.assertRaisesRegex(AssertionError, "retained Phi1"):
            self.verify()

    def test_late_access_cannot_relabel_previous_cycle(self) -> None:
        r = self.invalid()
        r[3] = str(int(r[3]) - 1)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "absolute fetch coordinates"):
            self.verify()

    def test_graphics_consumes_inserted_ff(self) -> None:
        r = next(
            r for r in self.rows[2:-1] if r[0] == "P1" and r[2] == "60" and r[3] == "24"
        )
        r[4] = r[5] = str(int(r[4]) - 8)
        # Keep source data and latch coherent, so the cache-consumption check must fail.
        self.coherent_data(r, self.graphics[int(r[4]) - 0x2000])
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(
            AssertionError, "matrix consumption / retained row"
        ):
            self.verify()

    def coherent_data(self, row: list[str], data: int) -> None:
        row[6] = str(data)
        after = False
        for r in self.rows[self.rows.index(row) + 1 : -1]:
            if r[0] == "L1":
                if after:
                    break
                r[6] = str(data)
                after = True
            r[10] = str(data)

    def test_next_line_retains_inserted_ff(self) -> None:
        r = next(
            r for r in self.rows[2:-1] if r[0] == "P1" and r[2] == "61" and r[3] == "24"
        )
        r[4] = r[5] = str(0x2000 + self.matrix[49] * 8 + 2)
        self.coherent_data(r, self.graphics[int(r[4]) - 0x2000])
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(
            AssertionError, "matrix consumption / retained row"
        ):
            self.verify()

    def test_last_slot_does_not_read_ram(self) -> None:
        self.load(15, 0)
        r = self.invalid()
        self.assertEqual(r[3], "53")
        r[0] = "P2"
        r[5] = r[4]
        r[6] = str(self.matrix[int(r[4]) - 0x400])
        r[8] = "0"
        with self.assertRaisesRegex(AssertionError, "matrix ownership countdown"):
            self.verify()

    def test_control_cannot_create_dma(self) -> None:
        self.load(force=False)
        source = next(r for r in self.rows[2:-1] if r[0] == "P2")
        injected = source.copy()
        latch = next(
            r for r in self.rows[2:-1] if r[0] == "L1" and r[2] == "60" and r[3] == "23"
        )
        injected[1:4] = latch[1:4]
        injected[10] = latch[10]
        self.rows.insert(self.rows.index(latch) + 1, injected)
        self.rows[-1][1] = str(len(self.rows) - 3)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "unexpected matrix slot"):
            self.verify()

    def test_coherently_shifted_cpu_event(self) -> None:
        match = list(re.finditer("Trace store d011" + EVENT, self.log))[-1]
        _y, c, _a, t = match.groups()
        text = match.group(0)
        changed = text.replace(
            f"{int(c)}/$" + f"{int(c):02x}", f"{int(c) + 1}/$" + f"{int(c) + 1:02x}"
        ).replace(t, str(int(t) + 1))
        self.log = self.log[: match.start()] + changed + self.log[match.end() :]
        self.case["writes"][-1][1] += 1
        self.case["writes"][-1][3] += 1
        with self.assertRaisesRegex(AssertionError, "unexpected matrix slot"):
            self.verify()

    def test_missing_completion(self) -> None:
        self.log = self.log.replace("Stop on store d7ff", "removed")
        with self.assertRaisesRegex(AssertionError, "completion event"):
            self.verify()

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(AssertionError, "matrix case coverage"):
            verify_coverage(self.cases[:-1])

    def test_duplicate_case(self) -> None:
        self.cases[-1] = self.cases[0]
        with self.assertRaisesRegex(AssertionError, "matrix case coverage"):
            verify_coverage(self.cases)

    def test_empty_cases(self) -> None:
        with self.assertRaisesRegex(AssertionError, "matrix case coverage"):
            verify_coverage([])


if __name__ == "__main__":
    unittest.main()
