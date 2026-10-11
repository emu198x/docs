import gzip
import unittest
from pathlib import Path

from capture import verify


class CombinedGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with gzip.open(Path(__file__).with_name("baseline.txt.gz"), "rt") as stream:
            cls.rows = stream.readlines()

    def changed(self, prefix: str, column: int, value: str) -> str:
        fields = next(row for row in self.rows if row.startswith(prefix)).split()
        self.assertNotEqual(fields[column], value)
        fields[column] = value
        return " ".join(fields)

    def test_complete(self) -> None:
        self.assertEqual(verify(self.rows), {"cases": 768, "observations": 5376})

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete combined inventory"):
            verify([])

    def test_missing_observation(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete combined inventory"):
            verify(self.rows[:-1])

    def test_duplicate_observation(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate combined observation"):
            verify([self.rows[0], self.rows[0]])

    def test_lost_delivery(self) -> None:
        with self.assertRaisesRegex(ValueError, "combined mismatch"):
            verify([self.changed("0 3 0 64 0 0 0 0 64 1 ", 15, "9124416")])

    def test_lost_order(self) -> None:
        with self.assertRaisesRegex(ValueError, "combined mismatch"):
            verify([self.changed("0 3 0 64 0 0 0 0 64 1 ", 15, "9418752")])

    def test_lost_charge(self) -> None:
        with self.assertRaisesRegex(ValueError, "combined mismatch"):
            verify([self.changed("0 0 0 64 0 0 0 0 64 1 ", 15, "0")])

    def test_untouched_channel(self) -> None:
        with self.assertRaisesRegex(ValueError, "combined mismatch"):
            verify([self.changed("0 0 0 64 0 0 0 0 64 1 ", 11, "1")])


if __name__ == "__main__":
    unittest.main()
