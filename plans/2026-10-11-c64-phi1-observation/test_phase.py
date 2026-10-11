"""Falsify shifted, missing and internally inconsistent store traces."""

from __future__ import annotations

import gzip
import json
import re
import unittest
from pathlib import Path

from bank_phase import EVENT, analyse

ROOT = Path(__file__).parent


class PhaseGuards(unittest.TestCase):
    def setUp(self) -> None:
        self.logs = json.loads(
            gzip.decompress((ROOT / "phase-logs.json.gz").read_bytes())
        )

    def test_all_profiles_and_window_mutations(self) -> None:
        results = [
            analyse(model, self.logs[model], ROOT / "transient-native")
            for model in ("pal", "c64c", "ntsc", "c64cntsc", "oldntsc")
        ]
        self.assertEqual(sum(r["glyph_cells"] for r in results), 40000)
        self.assertEqual(sum(r["stores"] for r in results), 40965)
        self.assertEqual(sum(r["two_clock_window_mismatches"] for r in results), 4121)
        self.assertTrue(all(r["shifted_clock_mismatches"]["0"] == 0 for r in results))

    def test_empty_trace(self) -> None:
        with self.assertRaises(AssertionError):
            analyse("pal", "", ROOT / "transient-native")

    def test_missing_store(self) -> None:
        log = re.sub("Trace store dd00" + EVENT, "", self.logs["pal"], count=1)
        with self.assertRaises(AssertionError):
            analyse("pal", log, ROOT / "transient-native")

    def test_wrong_control(self) -> None:
        with self.assertRaises(AssertionError):
            analyse(
                "pal",
                self.logs["pal"].replace("GlueLogic=1", "GlueLogic=0"),
                ROOT / "transient-native",
            )

    def test_wrong_bank_sequence(self) -> None:
        with self.assertRaises(AssertionError):
            analyse(
                "pal",
                self.logs["pal"].replace("A:02", "A:03", 1),
                ROOT / "transient-native",
            )

    def test_missing_completion(self) -> None:
        with self.assertRaises(AssertionError):
            analyse(
                "pal",
                self.logs["pal"].replace("Stop on store d7ff", "removed"),
                ROOT / "transient-native",
            )

    def test_coherently_shifted_cpu_stores(self) -> None:
        # Advance every trace clock by one and update decimal/hex raster fields
        # consistently. Clock self-consistency alone cannot reject this lie;
        # the independently captured bank-3 pixel mask must do so.
        pattern = re.compile("Trace store dd00" + EVENT)

        def shift(match: re.Match[str]) -> str:
            clock = int(match.group(4)) + 1
            line, cycle = (clock // 63) % 312, clock % 63
            original = match.group(0)
            _header, instruction = original.split("\n", 1)
            instruction = re.sub(r"\d+\n$", f"{clock}\n", instruction)
            return (
                f"Trace store dd00) {line}/$ {line:03x}, {cycle}/$ {cycle:02x}\n".replace(
                    "$ ", "$"
                )
                + instruction
            )

        log = pattern.sub(shift, self.logs["pal"])
        self.assertEqual(len(pattern.findall(log)), 8193)
        with self.assertRaisesRegex(AssertionError, r"'0': [1-9]"):
            analyse("pal", log, ROOT / "transient-native")


if __name__ == "__main__":
    unittest.main()
