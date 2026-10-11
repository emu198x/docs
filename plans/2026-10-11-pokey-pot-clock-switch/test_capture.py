import gzip
import unittest
from pathlib import Path

from capture import verify


class ClockSwitchGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with gzip.open(Path(__file__).with_name("baseline.txt.gz"), "rt") as stream:
            cls.rows = stream.readlines()

    def changed(self, prefix: str, tick: int, value: str) -> str:
        fields = next(row for row in self.rows if row.startswith(prefix)).split()
        self.assertNotEqual(fields[5 + tick], value)
        fields[5 + tick] = value
        return " ".join(fields)

    def test_complete(self) -> None:
        self.assertEqual(
            verify(self.rows), {"cases": 144, "clocks": 3888432, "pot_reads": 31107456}
        )

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete clock-switch inventory"):
            verify([])

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete clock-switch inventory"):
            verify(self.rows[:-1])

    def test_duplicate_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate clock-switch case"):
            verify([self.rows[0], self.rows[0]])

    def test_missing_clock(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete clock trace"):
            verify([self.rows[0].rsplit(" ", 1)[0]])

    def test_lost_delay(self) -> None:
        with self.assertRaisesRegex(ValueError, "clock-switch mismatch"):
            verify([self.changed("CASE 0 4 0 16 ", 17, "0:255:1:1")])

    def test_wrong_resume_phase(self) -> None:
        with self.assertRaisesRegex(ValueError, "clock-switch mismatch"):
            verify([self.changed("CASE 0 3 0 16 ", 96, "1:255:1:1")])

    def test_lost_slow_phase(self) -> None:
        with self.assertRaisesRegex(ValueError, "clock-switch mismatch"):
            verify([self.changed("CASE 4 3 0 16 ", 97, "16:255:16:1")])


if __name__ == "__main__":
    unittest.main()
