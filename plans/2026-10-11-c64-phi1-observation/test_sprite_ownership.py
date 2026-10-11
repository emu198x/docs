"""Reject missing ownership, false physical reads and unqualified CPU timing."""

from __future__ import annotations

import csv
import io
import json
import unittest
import zipfile
from pathlib import Path

from verify_fetch_trace import verify_rows
from verify_sprite_ownership import verify_archive, verify_case, verify_coverage

ARCHIVE = Path(__file__).with_name("ownership-native.zip")


class SpriteOwnershipGuards(unittest.TestCase):
    def setUp(self) -> None:
        with zipfile.ZipFile(ARCHIVE) as archive:
            self.cases = json.loads(archive.read("capture.json"))["rows"]
            self.case = next(
                c
                for c in self.cases
                if (c["model"], c["bank"], c["delay"]) == ("pal", 0, 15)
            )
            self.rows = list(
                csv.reader(
                    io.StringIO(archive.read("pal-bank0-delay15-phase0.csv").decode())
                )
            )
            self.log = archive.read("pal-bank0-delay15-phase0.log").decode()
        self.invalid = next(r for r in self.rows if r[0] == "S0I")

    def verify(self) -> dict:
        return verify_case(self.case, self.rows, self.log)

    def test_all_native_boundaries(self) -> None:
        result = verify_archive(ARCHIVE)
        self.assertEqual(result["states"], {"early": 40, "invalid": 20, "late": 40})
        self.assertEqual(result["sprite_bytes"], 3780)
        self.assertEqual(result["invalid_bytes"], 20)

    def test_unconditional_ram_access(self) -> None:
        self.invalid[0] = "P2"
        self.invalid[5] = str(int(self.invalid[4]))
        self.invalid[6] = str(self.case["ram"][0])
        verify_rows(
            self.rows, 63
        )  # A structurally sound trace can use the wrong source.
        with self.assertRaisesRegex(AssertionError, "missing invalid access"):
            self.verify()

    def test_ram_byte_substituted_for_bus(self) -> None:
        self.invalid[6] = self.invalid[11] = str(self.case["ram"][0])
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "substituted bus byte"):
            self.verify()

    def test_invalid_access_omitted(self) -> None:
        self.rows.remove(self.invalid)
        self.rows[-1] = ["END", str(len(self.rows) - 3)]
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "DMA coverage"):
            self.verify()

    def test_invalid_access_overwrites_phi1(self) -> None:
        self.invalid[10] = self.invalid[6]
        with self.assertRaisesRegex(AssertionError, "retained Phi1 changed"):
            self.verify()

    def test_wrong_invalid_phase(self) -> None:
        self.invalid[3] = str(int(self.invalid[3]) + 1)
        with self.assertRaisesRegex(AssertionError, "Phi2 clock"):
            self.verify()

    def test_ownership_delay_wrong(self) -> None:
        self.invalid[8] = "2"
        with self.assertRaisesRegex(AssertionError, "missing invalid access"):
            self.verify()

    def test_wrong_actual_ram_byte(self) -> None:
        row = next(r for r in self.rows if r[0] == "P2")
        row[6] = str(int(row[6]) ^ 1)
        with self.assertRaisesRegex(AssertionError, "RAM byte"):
            self.verify()

    def test_wrong_actual_bank(self) -> None:
        row = next(r for r in self.rows if r[0] == "P2")
        row[5] = str(int(row[5]) + 0x4000)
        with self.assertRaisesRegex(AssertionError, "physical bank"):
            self.verify()

    def test_missing_cpu_store(self) -> None:
        self.log = self.log.replace("Trace store d015", "removed", 1)
        with self.assertRaisesRegex(AssertionError, "CPU store coverage"):
            self.verify()

    def test_missing_completion(self) -> None:
        self.log = self.log.replace("Stop on store d7ff", "removed")
        with self.assertRaisesRegex(AssertionError, "completion event"):
            self.verify()

    def test_fabricated_cpu_clock(self) -> None:
        self.case["writes"][1][3] -= 1
        with self.assertRaisesRegex(AssertionError, "CPU store coverage"):
            self.verify()

    def test_missing_bank_case(self) -> None:
        with self.assertRaisesRegex(AssertionError, "case coverage"):
            verify_coverage(self.cases[:-1])

    def test_duplicate_case(self) -> None:
        self.cases[-1] = self.cases[0]
        with self.assertRaisesRegex(AssertionError, "case coverage"):
            verify_coverage(self.cases)

    def test_wrong_source_ram(self) -> None:
        self.case["ram"][0] = 255
        with self.assertRaisesRegex(AssertionError, "source RAM"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
