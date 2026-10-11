import gzip
import unittest
from pathlib import Path

from capture import verify


class BorrowGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = gzip.decompress(
            Path(__file__).with_name("baseline.txt.gz").read_bytes()
        ).decode()

    def test_complete_recorded_capture(self) -> None:
        result = verify(self.capture)
        self.assertEqual(result["cases"], 576)
        self.assertEqual(result["timer_events"], 210884)
        self.assertEqual(result["output_transitions"], 26318)

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete timer case inventory"):
            verify("")

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete timer case inventory"):
            verify("\n".join(self.capture.splitlines()[1:]))

    def test_duplicate_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            verify(self.capture + self.capture.splitlines()[0] + "\n")

    def test_first_borrow_shift(self) -> None:
        with self.assertRaisesRegex(ValueError, "first borrow deadline mismatch"):
            verify(self.capture.replace("1000 1031 1031", "1000 1028 1031", 1))

    def test_output_shift(self) -> None:
        with self.assertRaisesRegex(ValueError, "borrow-to-output delay mismatch"):
            verify(self.capture.replace("O2066:0", "O2064:0", 1))

    def test_dropped_irq(self) -> None:
        with self.assertRaisesRegex(ValueError, "IRQ delivery differs"):
            verify(self.capture.replace(" I1031:254", "", 1))


if __name__ == "__main__":
    unittest.main()
