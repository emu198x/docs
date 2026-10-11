"""Negative controls for the retained Phi1 observation parser."""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from run_probe import analyse

ROOT = Path(__file__).parent


class ProbeGuards(unittest.TestCase):
    def setUp(self) -> None:
        self.log = (ROOT / "run.log").read_text()
        self.reference = json.loads((ROOT / "native/comparison.json").read_text())
        self.first = next(
            line for line in self.log.splitlines() if line.startswith("ROW|")
        )

    def test_retained_red_run(self) -> None:
        result = analyse(self.log, self.reference, 101)
        self.assertEqual((result["samples"], result["mismatches"]), (512, 468))

    def test_matching_native_rows_pass(self) -> None:
        lines = []
        for r in self.reference["rows"]:
            if r["model"] != "oldntsc":
                status = 0 if r["endpoint"] == "io1" else 255
                lines.append(
                    f"ROW|{r['model']}|{r['endpoint']}|{status}|0|{r['actual']}"
                )
        self.assertEqual(analyse("\n".join(lines), self.reference, 0)["mismatches"], 0)

    def test_empty_log_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            analyse("", self.reference, 0)

    def test_missing_model_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            analyse(self.log.replace(self.first, ""), self.reference, 101)

    def test_duplicate_model_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            analyse(self.log + "\n" + self.first, self.reference, 101)

    def test_short_measurement_rejected(self) -> None:
        prefix, values = self.first.rsplit("|", 1)
        changed = prefix + "|" + str(ast.literal_eval(values)[:-1])
        with self.assertRaises(AssertionError):
            analyse(self.log.replace(self.first, changed), self.reference, 101)

    def test_fabricated_zero_count_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            analyse(self.log.replace("|53|", "|0|"), self.reference, 101)

    def test_unexpected_process_exit_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            analyse(self.log, self.reference, 0)

    def test_invalid_byte_rejected(self) -> None:
        prefix, values = self.first.rsplit("|", 1)
        values = ast.literal_eval(values)
        values[0] = 256
        with self.assertRaises(AssertionError):
            analyse(
                self.log.replace(self.first, prefix + "|" + str(values)),
                self.reference,
                101,
            )


if __name__ == "__main__":
    unittest.main()
