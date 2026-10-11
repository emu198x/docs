import unittest
from pathlib import Path

from capture import verify


class ResetGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = Path(__file__).with_name("baseline.txt").read_text()

    def test_complete_capture(self) -> None:
        result = verify(self.capture)
        self.assertEqual(result["cases"], 1440)
        self.assertEqual(result["timer_events"], 7560)
        self.assertEqual(result["irq_calls"], 5172)
        self.assertEqual(result["reset_calls"], 1080)

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete STIMER case inventory"):
            verify("")

    def test_missing(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete STIMER case inventory"):
            verify("\n".join(self.capture.splitlines()[1:]))

    def test_duplicate(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate STIMER case"):
            verify(self.capture + self.capture.splitlines()[0] + "\n")

    def test_reset_shift(self) -> None:
        with self.assertRaisesRegex(ValueError, "reset delivery mismatch"):
            verify(self.capture.replace("R1897", "R1898", 1))

    def test_dropped_irq(self) -> None:
        with self.assertRaisesRegex(ValueError, "STIMER IRQ delivery mismatch"):
            verify(self.capture.replace(" I1899:254", "", 1))

    def test_borrow_shift(self) -> None:
        with self.assertRaisesRegex(ValueError, "reset borrow mismatch"):
            verify(self.capture.replace("E1899:0", "E1898:0", 1))

    def test_write_shift(self) -> None:
        with self.assertRaisesRegex(ValueError, "wrong STIMER input coordinates"):
            verify(self.capture.replace("1899 1893", "1899 1894", 1))

    def test_retrigger_not_coalesced(self) -> None:
        row = next(
            line
            for line in self.capture.splitlines()
            if line.startswith("CASE 0 0 0 -6 3 ")
        )
        changed = row.replace("R1899", "R1897")
        self.assertNotEqual(changed, row)
        with self.assertRaisesRegex(ValueError, "reset delivery mismatch"):
            verify(self.capture.replace(row, changed, 1))


if __name__ == "__main__":
    unittest.main()
