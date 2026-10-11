import gzip
import itertools
import unittest
from collections.abc import Iterator
from pathlib import Path

from capture import verify


def rows() -> Iterator[str]:
    with gzip.open(Path(__file__).with_name("baseline.txt.gz"), "rt") as capture:
        yield from capture


class LinkedGuards(unittest.TestCase):
    def test_complete(self) -> None:
        result = verify(rows())
        self.assertEqual(result["cases"], 6912)
        self.assertEqual(result["timer_events"], 2532866)
        self.assertEqual(result["irq_calls"], 1285651)
        self.assertEqual(result["reset_calls"], 5184)
        self.assertEqual(result["output_transitions"], 1158200)

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete linked reset inventory"):
            verify([])

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete linked reset inventory"):
            verify(itertools.islice(rows(), 1, None))

    def test_duplicate_case(self) -> None:
        first = next(rows())
        with self.assertRaisesRegex(ValueError, "duplicate linked reset case"):
            verify(itertools.chain([first], rows()))

    def test_high_borrow_phase(self) -> None:
        first = next(rows())
        changed = first.replace("E1034:1", "E1031:1", 1)
        self.assertNotEqual(first, changed)
        with self.assertRaisesRegex(ValueError, "linked borrow sequence mismatch"):
            verify([changed])

    def test_lost_high_irq(self) -> None:
        first = next(rows())
        changed = first.replace(" I1034:253", "", 1)
        self.assertNotEqual(first, changed)
        with self.assertRaisesRegex(ValueError, "linked IRQ mismatch"):
            verify([changed])

    def test_reset_phase(self) -> None:
        row = next(line for line in rows() if line.startswith("CASE 0 0 0 0 0 -6 1 "))
        changed = row.replace("R1057", "R1058", 1)
        self.assertNotEqual(row, changed)
        with self.assertRaisesRegex(ValueError, "linked reset delivery mismatch"):
            verify([changed])

    def test_lost_output(self) -> None:
        first = next(rows())
        changed = first.replace(" O2000:1", "", 1)
        self.assertNotEqual(first, changed)
        with self.assertRaisesRegex(ValueError, "linked waveform mismatch"):
            verify([changed])


if __name__ == "__main__":
    unittest.main()
