import gzip
import unittest
from pathlib import Path

from capture import verify


class RestartGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with gzip.open(Path(__file__).with_name("baseline.txt.gz"), "rt") as stream:
            cls.rows = stream.readlines()

    def changed(self, prefix: str, column: int, value: str) -> list[str]:
        result = self.rows.copy()
        index = next(i for i, row in enumerate(result) if row.startswith(prefix))
        fields = result[index].split()
        self.assertNotEqual(fields[column], value)
        fields[column] = value
        result[index] = " ".join(fields)
        return result

    def test_complete(self) -> None:
        self.assertEqual(
            verify(self.rows),
            {"cases": 288, "observations": 16512, "pot_reads": 132096},
        )

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete restart inventory"):
            verify([])

    def test_missing_observation(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete restart inventory"):
            verify(self.rows[:-1])

    def test_duplicate_observation(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate observation"):
            verify([self.rows[0], self.rows[0]])

    def test_restart_discards_charge(self) -> None:
        with self.assertRaisesRegex(ValueError, "restart mismatch"):
            verify(self.changed("0 0 8 0 64 64 1 ", 11, "0"))

    def test_preset_discards_latch(self) -> None:
        with self.assertRaisesRegex(ValueError, "restart mismatch"):
            verify(self.changed("0 0 8 1 64 0 0 ", 7, "0"))

    def test_early_master_stop(self) -> None:
        with self.assertRaisesRegex(ValueError, "restart mismatch"):
            verify(self.changed("0 0 8 0 64 15 0 ", 10, "0"))

    def test_discharge_missing(self) -> None:
        with self.assertRaisesRegex(ValueError, "restart mismatch"):
            verify(self.changed("3 0 8 0 27000 27000 0 ", 11, "2523293286"))


if __name__ == "__main__":
    unittest.main()
