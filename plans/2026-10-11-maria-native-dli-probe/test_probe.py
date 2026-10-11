"""Reject incomplete captures and failures disguised as passing evidence."""

import unittest
from pathlib import Path

from run_probe import summarize


class CaptureGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.log = Path(__file__).with_name("baseline.log").read_text()
        cls.row = next(
            line for line in cls.log.splitlines() if line.startswith("region=")
        )

    def test_complete_recorded_capture(self) -> None:
        result = summarize(self.log, 101)
        self.assertEqual((result["cases"], result["mismatches"]), (192, 6))

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete case inventory"):
            summarize(self.log.replace(self.row + "\n", "", 1), 101)

    def test_duplicate_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            summarize(self.log + self.row + "\n", 101)

    def test_no_execution(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete case inventory"):
            summarize("compiler failed\n", 101)

    def test_false_success_status(self) -> None:
        with self.assertRaisesRegex(ValueError, "cargo status"):
            summarize(self.log, 0)

    def test_no_active_dma(self) -> None:
        changed = self.log.replace(
            "enabled=false descriptors=0", "enabled=true descriptors=0", 1
        )
        with self.assertRaisesRegex(ValueError, "missing active DMA"):
            summarize(changed, 101)

    def test_missing_test_result(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing executed test result"):
            summarize(self.log.replace("test result:", "lost result:"), 101)

    def test_falsified_summary(self) -> None:
        with self.assertRaisesRegex(ValueError, "completion summary"):
            summarize(
                self.log.replace("cases=192 mismatches=6", "cases=192 mismatches=0"),
                101,
            )


if __name__ == "__main__":
    unittest.main()
