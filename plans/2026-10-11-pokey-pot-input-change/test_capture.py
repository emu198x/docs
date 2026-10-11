import gzip
import unittest
from pathlib import Path

from capture import verify


class InputGuards(unittest.TestCase):
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
        self.assertEqual(verify(self.rows), {"cases": 1920, "observations": 60288})

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete input inventory"):
            verify([])

    def test_missing_observation(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete input inventory"):
            verify(self.rows[:-1])

    def test_duplicate_observation(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate input observation"):
            verify([self.rows[0], self.rows[0]])

    def test_lost_charge(self) -> None:
        with self.assertRaisesRegex(ValueError, "input mismatch"):
            verify([self.changed("0 0 64 1 64 0 64 1 ", 13, "0")])

    def test_lost_rearm(self) -> None:
        with self.assertRaisesRegex(ValueError, "input mismatch"):
            verify([self.changed("0 0 64 3 8192 0 8192 1 ", 10, "0")])

    def test_immediate_update(self) -> None:
        with self.assertRaisesRegex(ValueError, "input mismatch"):
            verify([self.changed("0 0 64 1 8192 0 8192 1 ", 8, "1")])

    def test_other_input_corruption(self) -> None:
        with self.assertRaisesRegex(ValueError, "input mismatch"):
            verify([self.changed("0 0 64 3 8192 0 8192 1 ", 14, "0")])


if __name__ == "__main__":
    unittest.main()
