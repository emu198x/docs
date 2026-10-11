"""Exercise comparator rejection and mismatch detection against complete traces."""

import tempfile
import unittest
from pathlib import Path

from compare import KINDS, compare

ROOT = Path(__file__).resolve().parent


class ComparatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = (ROOT / "reference.txt").read_text()
        cls.first, cls.rest = cls.reference.split("\n", 1)
        cls.inputs = ROOT / "cases.txt"
        cls.refs = ROOT / "reference.txt"

    def check_mutation(self, transform) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            actual = Path(tmp) / "actual.txt"
            actual.write_text(transform(self.first) + "\n" + self.rest)
            return compare(self.inputs, self.refs, actual)["counts"]

    def test_reference_control(self) -> None:
        result = compare(self.inputs, self.refs, self.refs)
        self.assertEqual(result["counts"]["exact"], 96800)
        self.assertEqual(
            {k: result["counts"][k] for k in KINDS}, dict.fromkeys(KINDS, 0)
        )

    def test_empty_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.txt"
            empty.write_text("")
            with self.assertRaisesRegex(ValueError, "incomplete case coverage"):
                compare(empty, empty, empty)

    def test_missing_row_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            truncated = Path(tmp) / "truncated.txt"
            truncated.write_text(self.rest)
            with self.assertRaisesRegex(ValueError, "key mismatch"):
                compare(self.inputs, self.refs, truncated)
            truncated.write_text(
                self.reference[: self.reference.rfind("\n", 0, -1) + 1]
            )
            with self.assertRaisesRegex(ValueError, "shorter"):
                compare(self.inputs, self.refs, truncated)

    def test_duplicate_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inputs = Path(tmp) / "cases.txt"
            traces = Path(tmp) / "traces.txt"
            inputs.write_text((self.first.split("|")[0].strip() + "\n") * 2)
            traces.write_text((self.first + "\n") * 2)
            with self.assertRaisesRegex(ValueError, "duplicate input"):
                compare(inputs, traces, traces)

    def test_invalid_event_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid bus event"):
            self.check_mutation(lambda line: line.replace("r4000:60", "rgggg:60"))

    def test_register_mutation_detected(self) -> None:
        def mutate(line: str) -> str:
            parts = line.split("|")
            fields = parts[1].split()
            fields[1] = "01"
            parts[1] = " ".join(fields)
            return "|".join(parts)

        counts = self.check_mutation(mutate)
        self.assertEqual(counts["registers"], 1)
        self.assertEqual(counts["bus_trace"], 0)
        self.assertEqual(counts["exact"], 96799)

    def test_cycle_mutation_detected(self) -> None:
        def mutate(line: str) -> str:
            parts = line.split("|")
            fields = parts[1].split()
            fields[0] = str(int(fields[0]) + 1)
            parts[1] = " ".join(fields)
            parts[2] = parts[2].strip() + ",rffff:ed"
            return "|".join(parts)

        counts = self.check_mutation(mutate)
        self.assertEqual(counts["cycle_count"], 1)
        self.assertEqual(counts["bus_trace"], 1)
        self.assertEqual(counts["exact"], 96799)

    def test_write_mutation_detected(self) -> None:
        counts = self.check_mutation(lambda line: line.replace("w5010:9b", "w5010:9c"))
        self.assertEqual(counts["write_effects"], 1)
        self.assertEqual(counts["write_timing"], 1)
        self.assertEqual(counts["exact"], 96799)

    def test_current_fault_detected(self) -> None:
        result = compare(self.inputs, self.refs, ROOT / "before.txt")
        self.assertEqual(
            result["counts"],
            {
                "cases": 96800,
                "exact": 24,
                "halted": 0,
                "cycle_count": 0,
                "registers": 0,
                "bus_trace": 96776,
                "write_effects": 0,
                "write_timing": 88000,
            },
        )
        self.assertEqual(
            result["write_cycle_delta_actual_minus_reference"], {-2: 88000}
        )


if __name__ == "__main__":
    unittest.main()
