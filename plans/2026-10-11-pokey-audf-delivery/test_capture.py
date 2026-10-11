import unittest
from pathlib import Path

from capture import verify


class DeliveryGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = Path(__file__).with_name("baseline.txt").read_text()

    def test_complete_capture(self) -> None:
        result = verify(self.capture)
        self.assertEqual(result["cases"], 480)
        self.assertEqual(result["timer_events"], 1920)
        self.assertEqual(result["irq_calls"], 1344)
        self.assertEqual(result["output_transitions"], 1920)

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete AUDF case inventory"):
            verify("")

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete AUDF case inventory"):
            verify("\n".join(self.capture.splitlines()[1:]))

    def test_duplicate_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate AUDF case"):
            verify(self.capture + self.capture.splitlines()[0] + "\n")

    def test_write_time_shift(self) -> None:
        with self.assertRaisesRegex(ValueError, "wrong AUDF write time"):
            verify(self.capture.replace("-3 1028", "-3 1027", 1))

    def test_pending_borrow_shift(self) -> None:
        with self.assertRaisesRegex(ValueError, "AUDF borrow/reload mismatch"):
            verify(self.capture.replace("E1031:0", "E1030:0", 1))

    def test_dropped_irq(self) -> None:
        with self.assertRaisesRegex(ValueError, "AUDF IRQ delivery mismatch"):
            verify(self.capture.replace(" I1031:254", "", 1))

    def test_output_delay(self) -> None:
        with self.assertRaisesRegex(ValueError, "AUDF output delivery mismatch"):
            verify(self.capture.replace("O2066:0", "O2064:0", 1))

    def test_immediate_delivery(self) -> None:
        lines = self.capture.splitlines()
        early = next(line for line in lines if line.startswith("CASE 0 0 0 1 -2 "))
        late = next(line for line in lines if line.startswith("CASE 0 0 0 1 -1 "))
        replacement = " ".join(late.split()[:7] + early.split()[7:])
        with self.assertRaisesRegex(ValueError, "AUDF borrow/reload mismatch"):
            verify(self.capture.replace(late, replacement, 1))


if __name__ == "__main__":
    unittest.main()
