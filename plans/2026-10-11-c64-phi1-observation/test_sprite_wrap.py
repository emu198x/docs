"""Falsify row resets and phase/line relabelling at the native wrap boundary."""

from __future__ import annotations

import csv
import io
import json
import unittest
import zipfile
from pathlib import Path

from verify_fetch_trace import verify_rows
from verify_sprite_wrap import verify_archive, verify_case, verify_coverage

ARCHIVE = Path(__file__).with_name("wrap-native.zip")


class SpriteWrapGuards(unittest.TestCase):
    def setUp(self) -> None:
        with zipfile.ZipFile(ARCHIVE) as archive:
            self.cases = json.loads(archive.read("capture.json"))["rows"]
            self.case = next(
                c
                for c in self.cases
                if c["model"] == "pal"
                and c["bank"] == 0
                and c["delay"] == 20
                and not c["reverse"]
            )
            name = "pal-bank0-sprite2-delay20-phase0-reverse0"
            self.rows = list(
                csv.reader(io.StringIO(archive.read(name + ".csv").decode()))
            )
            self.log = archive.read(name + ".log").decode()
        self.wrapped = next(
            r for r in self.rows if r[0] == "P2" and int(r[4]) == 0x2082
        )

    def verify(self) -> dict:
        return verify_case(self.case, self.rows, self.log)

    def test_all_models_and_banks(self) -> None:
        result = verify_archive(ARCHIVE)
        self.assertEqual(result["sprite_bytes"], 5040)
        self.assertEqual(result["wrap_rows"], 1680)
        self.assertEqual(result["stalled_pairs"], 40)

    def test_phi2_must_keep_previous_cycle_label(self) -> None:
        self.wrapped[3] = "0"
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "absolute Phi2 cycle"):
            self.verify()

    def test_phi2_must_keep_previous_line_label(self) -> None:
        self.wrapped[2] = str(int(self.wrapped[2]) + 1)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "absolute Phi2 line"):
            self.verify()

    def test_wrapped_byte_one_clock_early(self) -> None:
        self.wrapped[1] = str(int(self.wrapped[1]) - 1)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "absolute Phi2 cycle"):
            self.verify()

    def test_mc_reset_on_wrap(self) -> None:
        self.wrapped[4] = self.wrapped[5] = str(0x2080)
        self.wrapped[6] = str(self.case["ram"][128])
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "latched pointer/MC source"):
            self.verify()

    def test_pointer_changes_mid_row(self) -> None:
        self.wrapped[4] = self.wrapped[5] = str(0x20C2)
        self.wrapped[6] = str(self.case["ram"][194])
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "latched pointer/MC source"):
            self.verify()

    def test_wrapped_byte_missing(self) -> None:
        self.rows.remove(self.wrapped)
        self.rows[-1] = ["END", str(len(self.rows) - 3)]
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "byte sequence"):
            self.verify()

    def test_wrong_wrapped_data(self) -> None:
        self.wrapped[6] = str(int(self.wrapped[6]) ^ 1)
        with self.assertRaisesRegex(AssertionError, "source byte"):
            self.verify()

    def test_wrong_wrapped_bank(self) -> None:
        self.wrapped[5] = str(int(self.wrapped[5]) + 0x4000)
        with self.assertRaisesRegex(AssertionError, "physical bank"):
            self.verify()

    def test_missing_cpu_store(self) -> None:
        self.log = self.log.replace("Trace store 07fa", "removed", 1)
        with self.assertRaisesRegex(AssertionError, "CPU store coverage"):
            self.verify()

    def test_missing_completion(self) -> None:
        self.log = self.log.replace("Stop on store d7ff", "removed")
        with self.assertRaisesRegex(AssertionError, "completion event"):
            self.verify()

    def test_missing_model_bank_case(self) -> None:
        with self.assertRaisesRegex(AssertionError, "wrap case coverage"):
            verify_coverage(self.cases[:-1])

    def test_duplicate_case(self) -> None:
        self.cases[-1] = self.cases[0]
        with self.assertRaisesRegex(AssertionError, "wrap case coverage"):
            verify_coverage(self.cases)

    def test_non_wrap_sprite_rejected(self) -> None:
        self.cases[0]["sprite"] = 0
        with self.assertRaisesRegex(AssertionError, "wrap case coverage"):
            verify_coverage(self.cases)


if __name__ == "__main__":
    unittest.main()
