import unittest
from pathlib import Path

from capture import verify


class OutputGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = Path(__file__).with_name("baseline.txt").read_text()

    def test_complete(self) -> None:
        result = verify(self.capture)
        self.assertEqual(result["cases"], 960)
        self.assertEqual(result["output_transitions"], 624)

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete reset-output inventory"):
            verify("")

    def test_missing(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete reset-output inventory"):
            verify("\n".join(self.capture.splitlines()[1:]))

    def test_duplicate(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate reset-output case"):
            verify(self.capture + self.capture.splitlines()[0] + "\n")

    def test_hidden_state(self) -> None:
        fields = self.capture.splitlines()[0].split()
        fields[8] = str(1 - int(fields[8]))
        with self.assertRaisesRegex(ValueError, "reset hidden-state mismatch"):
            verify(" ".join(fields) + "\n" + "\n".join(self.capture.splitlines()[1:]))

    def test_filter_latch(self) -> None:
        fields = self.capture.splitlines()[0].split()
        fields[9] = str(1 - int(fields[9]))
        with self.assertRaisesRegex(ValueError, "reset hidden-state mismatch"):
            verify(" ".join(fields) + "\n" + "\n".join(self.capture.splitlines()[1:]))

    def test_reset_time(self) -> None:
        row = next(
            line
            for line in self.capture.splitlines()
            if line.startswith("CASE 0 0 0 0 99 1 ")
        )
        changed = row.replace("2032:0", "2034:0")
        self.assertNotEqual(row, changed)
        with self.assertRaisesRegex(ValueError, "reset output timing mismatch"):
            verify(self.capture.replace(row, changed, 1))

    def test_volume_override(self) -> None:
        row = next(
            line
            for line in self.capture.splitlines()
            if line.startswith("CASE 0 0 0 1 99 1 ")
        )
        changed = row.replace("2000:1", "2000:0")
        self.assertNotEqual(row, changed)
        with self.assertRaisesRegex(ValueError, "reset output timing mismatch"):
            verify(self.capture.replace(row, changed, 1))


if __name__ == "__main__":
    unittest.main()
