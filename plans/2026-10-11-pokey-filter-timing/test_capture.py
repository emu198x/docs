"""Fail closed when timed reference captures lose cases or output timing."""

import unittest
from pathlib import Path

from capture import verify


class CaptureGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = Path(__file__).with_name("baseline.txt").read_text()

    def test_full_capture(self) -> None:
        result = verify(self.capture)
        self.assertEqual(result["cases"], 648)
        self.assertEqual(result["settled_half_cycle_pulses"], 120)

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete case inventory"):
            verify("\n".join(self.capture.splitlines()[1:]))

    def test_duplicate_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            verify(self.capture + self.capture.splitlines()[0] + "\n")

    def test_empty_capture(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete case inventory"):
            verify("")

    def test_missing_inputs(self) -> None:
        rows = self.capture.splitlines()
        fields = rows[0].split()
        fields[7] = "0"
        rows[0] = " ".join(fields)
        with self.assertRaisesRegex(ValueError, "missing event inventory"):
            verify("\n".join(rows))

    def test_partition_changes_output(self) -> None:
        rows = self.capture.splitlines()
        index = next(
            i for i, row in enumerate(rows) if row.startswith("CASE 0 0 0 1 0 1 ")
        )
        rows[index] = rows[index].replace("2024:1", "2026:1")
        self.assertNotEqual(rows[index], self.capture.splitlines()[index])
        with self.assertRaisesRegex(ValueError, "flush partition"):
            verify("\n".join(rows))

    def test_erased_filter_pulses(self) -> None:
        rows = self.capture.splitlines()
        index = next(
            i for i, row in enumerate(rows) if row.startswith("CASE 0 2 0 1 0 1 ")
        )
        rows[index] = " ".join(rows[index].split()[:9] + ["2000:0"])
        with self.assertRaisesRegex(ValueError, "missing settled half-cycle pulses"):
            verify("\n".join(rows))


if __name__ == "__main__":
    unittest.main()
