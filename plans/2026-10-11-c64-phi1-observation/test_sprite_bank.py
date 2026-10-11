"""Reject bank selection faults even when the generic trace remains coherent."""

from __future__ import annotations

import csv
import io
import json
import re
import unittest
import zipfile
from pathlib import Path

from bank_phase import EVENT
from sprite_bank import stem
from verify_fetch_trace import verify_rows
from verify_sprite_bank import (
    verify_archive,
    verify_case,
    verify_coverage,
    verify_sequence,
)

ARCHIVE = Path(__file__).with_name("sprite-bank-native.zip")
CALIBRATION = Path(__file__).with_name("sprite-bank-calibration.zip")


class SpriteBankGuards(unittest.TestCase):
    def setUp(self) -> None:
        self.load()

    def load(
        self, glue: int = 1, old: int = 1, new: int = 2, calibration: bool = False
    ) -> None:
        with zipfile.ZipFile(CALIBRATION if calibration else ARCHIVE) as archive:
            self.cases = json.loads(archive.read("capture.json"))["rows"]
            self.case = next(
                c
                for c in self.cases
                if c["model"] == "pal"
                and c["glue"] == glue
                and c["old"] == old
                and c["new"] == new
                and c["delay"] == (19 if calibration else 17)
                and c["phase"] == (0 if calibration else 3)
            )
            name = stem(self.case)
            self.rows = list(
                csv.reader(io.StringIO(archive.read(name + ".csv").decode()))
            )
            self.banks = [archive.read(name + f"-bank{b}.bin") for b in range(4)]
            self.pointers = [archive.read(name + f"-pointers{b}.bin") for b in range(4)]
            self.log = archive.read(name + ".log").decode()
        self.write_clock = self.case["writes"][-1][3]
        self.edge = next(
            r for r in self.rows[2:-1] if r[0] == "P1" and int(r[1]) == self.write_clock
        )

    def verify(self) -> dict:
        return verify_case(self.case, self.rows, self.banks, self.pointers, self.log)

    def bank(self, row: list[str], bank: int) -> None:
        row[5] = str(bank * 0x4000 + int(row[4]))

    def test_complete_transition_matrix(self) -> None:
        result = verify_archive(ARCHIVE)
        self.assertEqual(result["sprite_bytes"], 20160)
        self.assertEqual(result["stalled_pairs"], 160)
        self.assertEqual(result["transient_fetches"], 20)

    def test_calibrated_pointer_transients(self) -> None:
        result = verify_archive(CALIBRATION, True)
        self.assertEqual(result["cases"], 132)
        self.assertEqual(result["transient_pointers"], 13)
        self.assertEqual(result["mixed_rows"], 0)

    def test_lost_custom_glue_transient(self) -> None:
        self.bank(self.edge, 2)
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "CPU-clock physical bank"):
            self.verify()

    def test_stale_bank(self) -> None:
        self.bank(self.edge, 1)
        with self.assertRaisesRegex(AssertionError, "CPU-clock physical bank"):
            self.verify()

    def test_early_bank(self) -> None:
        row = next(
            r
            for r in self.rows[2:-1]
            if r[0] == "P1" and int(r[1]) == self.write_clock - 1
        )
        self.bank(row, 2)
        with self.assertRaisesRegex(AssertionError, "CPU-clock physical bank"):
            self.verify()

    def test_widened_transient(self) -> None:
        row = next(
            r
            for r in self.rows[2:-1]
            if r[0] == "P1" and int(r[1]) == self.write_clock + 1
        )
        self.bank(row, 3)
        with self.assertRaisesRegex(AssertionError, "CPU-clock physical bank"):
            self.verify()

    def test_discrete_glue_has_no_transient(self) -> None:
        self.load(glue=0)
        self.bank(self.edge, 3)
        with self.assertRaisesRegex(AssertionError, "CPU-clock physical bank"):
            self.verify()

    def test_ordinary_transition_has_no_transient(self) -> None:
        self.load(old=0, new=2)
        self.bank(self.edge, 3)
        with self.assertRaisesRegex(AssertionError, "CPU-clock physical bank"):
            self.verify()

    def test_no_change_keeps_selected_bank(self) -> None:
        self.load(old=1, new=1)
        self.bank(self.edge, 3)
        with self.assertRaisesRegex(AssertionError, "CPU-clock physical bank"):
            self.verify()

    def test_glue_resource_must_match(self) -> None:
        self.log = self.log.replace("GlueLogic=1", "GlueLogic=0")
        with self.assertRaisesRegex(AssertionError, "glue resource"):
            self.verify()

    def test_wrong_pointer_source(self) -> None:
        self.load(calibration=True)
        self.assertEqual(int(self.edge[9]) & 0xE00, 0x600)
        self.edge[6] = str(self.pointers[2][(int(self.edge[9]) >> 12) & 7])
        # Keep the generic fetch/latch pair and following retained byte coherent.
        after = False
        for r in self.rows[self.rows.index(self.edge) + 1 : -1]:
            if r[0] == "L1":
                if after:
                    break
                r[6] = self.edge[6]
                after = True
            r[10] = self.edge[6]
        verify_rows(self.rows, 63)
        with self.assertRaisesRegex(AssertionError, "CPU-clock pointer source"):
            verify_sequence(self.case, self.rows, self.banks, self.pointers, self.log)

    def test_old_bank_held_for_data(self) -> None:
        row = next(
            r for r in self.rows[2:-1] if r[0] == "P2" and int(r[1]) > self.write_clock
        )
        self.bank(row, 1)
        with self.assertRaisesRegex(AssertionError, "CPU-clock physical bank"):
            self.verify()

    def test_mc_resets_at_bank_change(self) -> None:
        row = next(
            r for r in self.rows[2:-1] if r[0] == "P2" and int(r[1]) > self.write_clock
        )
        row[4] = str(int(row[4]) - 30)
        self.bank(row, 2)
        with self.assertRaisesRegex(AssertionError, "held pointer / MC"):
            self.verify()

    def test_wrong_data_byte(self) -> None:
        row = next(
            r for r in self.rows[2:-1] if r[0] == "P2" and int(r[1]) > self.write_clock
        )
        row[6] = str(int(row[6]) ^ 1)
        with self.assertRaisesRegex(AssertionError, "source byte"):
            self.verify()

    def test_missing_data_byte(self) -> None:
        row = next(
            r for r in self.rows[2:-1] if r[0] == "P2" and int(r[1]) > self.write_clock
        )
        self.rows.remove(row)
        self.rows[-1][1] = str(len(self.rows) - 3)
        with self.assertRaisesRegex(AssertionError, "byte sequence"):
            self.verify()

    def test_phi2_must_preserve_phi1(self) -> None:
        row = next(r for r in self.rows[2:-1] if r[0] == "P2")
        row[10] = str(int(row[10]) ^ 1)
        with self.assertRaisesRegex(AssertionError, "retained Phi1"):
            self.verify()

    def test_missing_cpu_store(self) -> None:
        self.log = self.log.replace("Trace store dd00", "removed", 1)
        with self.assertRaisesRegex(AssertionError, "CPU store coverage"):
            self.verify()

    def test_coherently_shifted_cpu_store(self) -> None:
        # Change both metadata and independently parsed monitor coordinates.
        match = list(re.finditer("Trace store dd00" + EVENT, self.log))[-1]
        text = match.group(0)
        _y, c, _a, t = match.groups()
        changed = text.replace(
            f"{int(c)}/$" + f"{int(c):02x}", f"{int(c) + 1}/$" + f"{int(c) + 1:02x}"
        ).replace(t, str(int(t) + 1))
        self.assertNotEqual(text, changed)
        self.log = self.log[: match.start()] + changed + self.log[match.end() :]
        self.case["writes"][-1][1] += 1
        self.case["writes"][-1][3] += 1
        with self.assertRaisesRegex(AssertionError, "CPU-clock physical bank"):
            self.verify()

    def test_missing_completion(self) -> None:
        self.log = self.log.replace("Stop on store d7ff", "removed")
        with self.assertRaisesRegex(AssertionError, "completion event"):
            self.verify()

    def test_missing_transition(self) -> None:
        with self.assertRaisesRegex(AssertionError, "bank case coverage"):
            verify_coverage(self.cases[:-1])

    def test_duplicate_transition(self) -> None:
        self.cases[-1] = self.cases[0]
        with self.assertRaisesRegex(AssertionError, "bank case coverage"):
            verify_coverage(self.cases)

    def test_empty_capture(self) -> None:
        with self.assertRaisesRegex(AssertionError, "bank case coverage"):
            verify_coverage([])


if __name__ == "__main__":
    unittest.main()
