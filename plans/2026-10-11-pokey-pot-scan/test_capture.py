import gzip
import unittest
from pathlib import Path

from capture import verify


class PotGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with gzip.open(Path(__file__).with_name("baseline.txt.gz"), "rt") as stream:
            cls.rows = stream.readlines()

    def test_complete(self) -> None:
        self.assertEqual(
            verify(self.rows), {"cases": 16, "cycles": 416048, "pot_reads": 3328384}
        )

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete pot inventory"):
            verify([])

    def test_missing(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete pot inventory"):
            verify(self.rows[:-1])

    def test_duplicate(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate pot case"):
            verify([self.rows[0], self.rows[0]])

    def test_missing_cycle(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete cycle trace"):
            verify([self.rows[0].rsplit(" ", 1)[0]])

    def test_wrong_live_count(self) -> None:
        fields = self.rows[8].split()
        self.assertEqual(fields[7], "2:255")
        fields[7] = "228:255"
        with self.assertRaisesRegex(ValueError, "pot trace mismatch"):
            verify([" ".join(fields)])

    def test_late_completion(self) -> None:
        fields = self.rows[8].split()
        self.assertEqual(fields[234], "229:0")
        fields[234] = "229:255"
        with self.assertRaisesRegex(ValueError, "pot trace mismatch"):
            verify([" ".join(fields)])

    def test_initialization_counts(self) -> None:
        fields = self.rows[0].split()
        self.assertEqual(fields[117], "0:255")
        fields[117] = "1:255"
        with self.assertRaisesRegex(ValueError, "pot trace mismatch"):
            verify([" ".join(fields)])


if __name__ == "__main__":
    unittest.main()
